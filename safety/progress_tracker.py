#!/usr/bin/env python3
"""
Progress Tracking System
Tracks refactoring progress and validates against safety criteria
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import sys

class RefactoringProgressTracker:
    def __init__(self, progress_file="refactoring_progress.json"):
        self.progress_file = Path(__file__).parent / progress_file
        self.progress_data = self.load_progress()
    
    def load_progress(self) -> Dict[str, Any]:
        """Load existing progress or create new"""
        if self.progress_file.exists():
            with open(self.progress_file) as f:
                return json.load(f)
        else:
            return {
                "start_date": datetime.now().isoformat(),
                "current_phase": 1,
                "current_sprint": 1,
                "sprints": {},
                "safety_checks": {},
                "metrics": {
                    "visual_changes": 0,
                    "api_changes": 0,
                    "performance_degradations": 0,
                    "test_failures": 0
                }
            }
    
    def save_progress(self):
        """Save progress to file"""
        with open(self.progress_file, 'w') as f:
            json.dump(self.progress_data, f, indent=2)
    
    def start_sprint(self, sprint_number: int, sprint_name: str):
        """Mark the start of a new sprint"""
        sprint_key = f"sprint_{sprint_number}"
        self.progress_data["sprints"][sprint_key] = {
            "name": sprint_name,
            "start_time": datetime.now().isoformat(),
            "end_time": None,
            "status": "in_progress",
            "objectives": [],
            "completed_tasks": [],
            "issues": [],
            "rollbacks": 0
        }
        self.progress_data["current_sprint"] = sprint_number
        self.save_progress()
        
        print(f"Started Sprint {sprint_number}: {sprint_name}")
    
    def add_objective(self, objective: str, sprint_number: Optional[int] = None):
        """Add an objective to the current or specified sprint"""
        if sprint_number is None:
            sprint_number = self.progress_data["current_sprint"]
        
        sprint_key = f"sprint_{sprint_number}"
        if sprint_key in self.progress_data["sprints"]:
            self.progress_data["sprints"][sprint_key]["objectives"].append({
                "description": objective,
                "added_at": datetime.now().isoformat(),
                "completed": False
            })
            self.save_progress()
            print(f"Added objective to Sprint {sprint_number}: {objective}")
    
    def complete_task(self, task_description: str, sprint_number: Optional[int] = None):
        """Mark a task as completed"""
        if sprint_number is None:
            sprint_number = self.progress_data["current_sprint"]
        
        sprint_key = f"sprint_{sprint_number}"
        if sprint_key in self.progress_data["sprints"]:
            self.progress_data["sprints"][sprint_key]["completed_tasks"].append({
                "description": task_description,
                "completed_at": datetime.now().isoformat()
            })
            
            # Check if this completes an objective
            for obj in self.progress_data["sprints"][sprint_key]["objectives"]:
                if task_description.lower() in obj["description"].lower():
                    obj["completed"] = True
            
            self.save_progress()
            print(f"✓ Completed: {task_description}")
    
    def record_issue(self, issue_description: str, severity: str = "minor"):
        """Record an issue encountered"""
        sprint_key = f"sprint_{self.progress_data['current_sprint']}"
        if sprint_key in self.progress_data["sprints"]:
            self.progress_data["sprints"][sprint_key]["issues"].append({
                "description": issue_description,
                "severity": severity,
                "recorded_at": datetime.now().isoformat(),
                "resolved": False
            })
            self.save_progress()
            print(f"⚠️  Issue recorded ({severity}): {issue_description}")
    
    def record_safety_check(self, check_name: str, passed: bool, details: Dict[str, Any] = None):
        """Record results of a safety check"""
        self.progress_data["safety_checks"][check_name] = {
            "passed": passed,
            "checked_at": datetime.now().isoformat(),
            "details": details or {}
        }
        
        # Update metrics based on check results
        if not passed:
            if "visual" in check_name.lower():
                self.progress_data["metrics"]["visual_changes"] += 1
            elif "api" in check_name.lower():
                self.progress_data["metrics"]["api_changes"] += 1
            elif "performance" in check_name.lower():
                self.progress_data["metrics"]["performance_degradations"] += 1
            elif "test" in check_name.lower():
                self.progress_data["metrics"]["test_failures"] += 1
        
        self.save_progress()
        status = "PASSED" if passed else "FAILED"
        print(f"Safety Check '{check_name}': {status}")
    
    def complete_sprint(self, sprint_number: Optional[int] = None):
        """Mark a sprint as completed"""
        if sprint_number is None:
            sprint_number = self.progress_data["current_sprint"]
        
        sprint_key = f"sprint_{sprint_number}"
        if sprint_key in self.progress_data["sprints"]:
            sprint = self.progress_data["sprints"][sprint_key]
            sprint["end_time"] = datetime.now().isoformat()
            sprint["status"] = "completed"
            
            # Calculate completion percentage
            total_objectives = len(sprint["objectives"])
            completed_objectives = sum(1 for obj in sprint["objectives"] if obj["completed"])
            completion_rate = (completed_objectives / total_objectives * 100) if total_objectives > 0 else 0
            
            sprint["completion_rate"] = completion_rate
            self.save_progress()
            
            print(f"\nSprint {sprint_number} Completed!")
            print(f"Completion Rate: {completion_rate:.1f}%")
            print(f"Tasks Completed: {len(sprint['completed_tasks'])}")
            print(f"Issues Encountered: {len(sprint['issues'])}")
    
    def generate_progress_report(self) -> str:
        """Generate a comprehensive progress report"""
        report = ["# FRC Scouting App Refactoring Progress Report"]
        report.append(f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Start Date: {self.progress_data['start_date']}")
        
        # Overall metrics
        report.append("\n## Overall Metrics")
        metrics = self.progress_data["metrics"]
        report.append(f"- Visual Changes Detected: {metrics['visual_changes']}")
        report.append(f"- API Changes Detected: {metrics['api_changes']}")
        report.append(f"- Performance Degradations: {metrics['performance_degradations']}")
        report.append(f"- Test Failures: {metrics['test_failures']}")
        
        # Safety checks summary
        report.append("\n## Safety Checks Summary")
        passed_checks = sum(1 for check in self.progress_data["safety_checks"].values() if check["passed"])
        total_checks = len(self.progress_data["safety_checks"])
        report.append(f"- Passed: {passed_checks}/{total_checks}")
        
        for check_name, check_data in self.progress_data["safety_checks"].items():
            status = "✓" if check_data["passed"] else "✗"
            report.append(f"  {status} {check_name}")
        
        # Sprint summaries
        report.append("\n## Sprint Progress")
        for sprint_key, sprint_data in sorted(self.progress_data["sprints"].items()):
            sprint_num = sprint_key.split('_')[1]
            report.append(f"\n### Sprint {sprint_num}: {sprint_data['name']}")
            report.append(f"- Status: {sprint_data['status']}")
            report.append(f"- Started: {sprint_data['start_time']}")
            if sprint_data['end_time']:
                report.append(f"- Completed: {sprint_data['end_time']}")
                report.append(f"- Completion Rate: {sprint_data.get('completion_rate', 0):.1f}%")
            
            # Objectives
            if sprint_data['objectives']:
                report.append("\n#### Objectives:")
                for obj in sprint_data['objectives']:
                    status = "✓" if obj['completed'] else "○"
                    report.append(f"  {status} {obj['description']}")
            
            # Issues
            if sprint_data['issues']:
                report.append("\n#### Issues:")
                for issue in sprint_data['issues']:
                    report.append(f"  - [{issue['severity'].upper()}] {issue['description']}")
        
        # Risk assessment
        report.append("\n## Risk Assessment")
        risk_score = (
            metrics['visual_changes'] * 10 +
            metrics['api_changes'] * 8 +
            metrics['performance_degradations'] * 5 +
            metrics['test_failures'] * 3
        )
        
        if risk_score == 0:
            risk_level = "LOW"
            risk_color = "green"
        elif risk_score < 10:
            risk_level = "MEDIUM"
            risk_color = "yellow"
        else:
            risk_level = "HIGH"
            risk_color = "red"
        
        report.append(f"- Overall Risk Level: **{risk_level}** (Score: {risk_score})")
        
        # Recommendations
        report.append("\n## Recommendations")
        if metrics['visual_changes'] > 0:
            report.append("- ⚠️  Visual changes detected - review and rollback if needed")
        if metrics['api_changes'] > 0:
            report.append("- ⚠️  API changes detected - ensure backward compatibility")
        if metrics['performance_degradations'] > 0:
            report.append("- ⚠️  Performance issues detected - investigate and optimize")
        if risk_score > 10:
            report.append("- 🛑 Consider halting refactoring and reviewing approach")
        
        return "\n".join(report)
    
    def save_report(self, filename: Optional[str] = None):
        """Save progress report to file"""
        if filename is None:
            filename = f"progress_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        
        report_path = Path("safety") / filename
        report_content = self.generate_progress_report()
        
        with open(report_path, 'w') as f:
            f.write(report_content)
        
        print(f"\nProgress report saved: {report_path}")
        return report_path
    
    def check_go_no_go_criteria(self) -> bool:
        """Check if it's safe to proceed with refactoring"""
        print("\n=== Go/No-Go Decision Criteria ===")
        
        criteria = {
            "No Visual Changes": self.progress_data["metrics"]["visual_changes"] == 0,
            "No API Breaking Changes": self.progress_data["metrics"]["api_changes"] == 0,
            "Performance Maintained": self.progress_data["metrics"]["performance_degradations"] == 0,
            "All Safety Checks Passed": all(
                check["passed"] for check in self.progress_data["safety_checks"].values()
            ),
            "No Critical Issues": not any(
                issue["severity"] == "critical" and not issue["resolved"]
                for sprint in self.progress_data["sprints"].values()
                for issue in sprint.get("issues", [])
            )
        }
        
        all_passed = all(criteria.values())
        
        for criterion, passed in criteria.items():
            status = "✓" if passed else "✗"
            print(f"  {status} {criterion}")
        
        if all_passed:
            print("\n✅ GO - Safe to proceed with next phase")
        else:
            print("\n🛑 NO-GO - Issues must be resolved before proceeding")
        
        return all_passed


def main():
    """Main entry point for progress tracking"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Refactoring Progress Tracker")
    parser.add_argument("--start-sprint", type=int, help="Start a new sprint")
    parser.add_argument("--sprint-name", type=str, help="Name for the new sprint")
    parser.add_argument("--complete-task", type=str, help="Mark a task as completed")
    parser.add_argument("--record-issue", type=str, help="Record an issue")
    parser.add_argument("--severity", type=str, choices=["minor", "major", "critical"], 
                       default="minor", help="Issue severity")
    parser.add_argument("--complete-sprint", action="store_true", help="Complete current sprint")
    parser.add_argument("--report", action="store_true", help="Generate progress report")
    parser.add_argument("--check-criteria", action="store_true", help="Check go/no-go criteria")
    
    args = parser.parse_args()
    
    tracker = RefactoringProgressTracker()
    
    if args.start_sprint and args.sprint_name:
        tracker.start_sprint(args.start_sprint, args.sprint_name)
    elif args.complete_task:
        tracker.complete_task(args.complete_task)
    elif args.record_issue:
        tracker.record_issue(args.record_issue, args.severity)
    elif args.complete_sprint:
        tracker.complete_sprint()
    elif args.report:
        tracker.save_report()
    elif args.check_criteria:
        tracker.check_go_no_go_criteria()
    else:
        # Show current status
        print(tracker.generate_progress_report())


if __name__ == "__main__":
    main()