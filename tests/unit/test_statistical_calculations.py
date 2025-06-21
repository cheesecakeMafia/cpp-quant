"""
Unit tests for statistical calculations in study_tracker.py
Tests progress calculations, project counting, and data aggregation
"""

import pytest
import json
import os
import tempfile
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch, MagicMock
from collections import defaultdict
import sys

# Add parent directory to path to import study_tracker
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from study_tracker import StudyTracker


class TestStatisticalCalculations:
    """Test statistical calculation accuracy and edge cases"""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test files"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def complex_markdown(self):
        """Complex markdown with projects and multiple phases"""
        return """# C++ Quantitative Finance Learning Path

## 📅 PHASE 1: C++ FUNDAMENTALS

### Week 1: Setup & C++ Basics
#### Day 1 (1 hour - Weekday)
- [x] Install g++ compiler and VS Code C++ extensions
- [x] Configure VS Code for C++ development
- [x] Create GitHub repo: "cpp-quant-journey"

#### Day 2 (1 hour - Weekday)
- [x] Watch: C++ Basics - Program Structure
- [x] Code: First "Hello World" program
- [ ] Practice: Compile and run from terminal

#### Day 3 (2 hours - Weekend)
- [x] Mini Project: Calculator with basic operations
- [ ] Test calculator with various inputs
- [ ] Document code and push to GitHub

### Week 2: Advanced Topics
#### Day 4 (1 hour - Weekday)
- [x] Watch: Variables and Data Types
- [x] Compare C++ types with Python types
- [ ] Code: Variable declaration exercises

#### Day 5 (2 hours - Weekend)
- [ ] Project: Trading Signal Generator
- [ ] Implement moving average calculation
- [ ] Add buy/sell signal logic

## 📅 PHASE 2: ADVANCED CONCEPTS

### Week 3: Object-Oriented Programming
#### Day 6 (1 hour - Weekday)
- [ ] Watch: Classes and Objects
- [ ] Code: Basic class implementation
- [ ] Practice: Constructor and destructor

#### Day 7 (2 hours - Weekend)
- [ ] Mini Project: Portfolio Class
- [ ] Implement portfolio tracking
- [ ] Add performance metrics
"""

    @pytest.fixture
    def tracker_with_complex_data(self, temp_dir, complex_markdown):
        """Create tracker with complex test data"""
        markdown_file = os.path.join(temp_dir, "complex_study_plan.md")
        progress_file = os.path.join(temp_dir, ".complex_progress.json")

        with open(markdown_file, "w") as f:
            f.write(complex_markdown)

        tracker = StudyTracker(markdown_file, progress_file)
        tracker.parse_markdown()
        return tracker

    def test_project_counting_accuracy(self, tracker_with_complex_data):
        """Test accurate counting of mini vs major projects"""
        tracker = tracker_with_complex_data
        
        # Count projects using the same logic as the main code
        mini_projects = 0
        major_projects = 0
        
        for cb in tracker.checkboxes:
            if cb["checked"] and "Mini Project:" in cb["content"]:
                mini_projects += 1
            elif (
                cb["checked"]
                and "Project:" in cb["content"]
                and "Mini" not in cb["content"]
            ):
                major_projects += 1

        # Verify counts match expected values from test data
        assert mini_projects == 1  # "Mini Project: Calculator"
        assert major_projects == 0  # "Project: Trading Signal Generator" is not checked

    def test_progress_percentage_calculation(self, tracker_with_complex_data):
        """Test progress percentage accuracy with various completion states"""
        tracker = tracker_with_complex_data
        
        total_tasks = len(tracker.checkboxes)
        completed_tasks = len([cb for cb in tracker.checkboxes if cb["checked"]])
        
        expected_percentage = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        
        # Should match expected calculation
        assert total_tasks > 0
        assert completed_tasks > 0
        assert 0 <= expected_percentage <= 100
        
        # Specific verification based on test data
        # From complex_markdown: 6 checked items out of ~16 total items
        assert expected_percentage > 30  # Should be significant progress
        assert expected_percentage < 60  # But not complete

    def test_week_progress_calculation(self, tracker_with_complex_data):
        """Test week progress calculation accuracy"""
        tracker = tracker_with_complex_data
        
        # Test Week 1 progress
        week1_items = [cb for cb in tracker.checkboxes if cb["week"] == 1]
        week1_completed = [cb for cb in week1_items if cb["checked"]]
        
        assert len(week1_items) > 0
        assert len(week1_completed) > 0
        
        week1_percentage = (len(week1_completed) / len(week1_items) * 100) if len(week1_items) > 0 else 0
        
        # Week 1 should have partial completion based on test data
        assert week1_percentage > 50  # More than half completed
        assert week1_percentage < 100  # But not fully completed

    def test_phase_progress_aggregation(self, tracker_with_complex_data):
        """Test multi-phase progress tracking"""
        tracker = tracker_with_complex_data
        
        # Calculate phase progress like the main code
        phase_progress = defaultdict(lambda: {"total": 0, "completed": 0})
        
        for cb in tracker.checkboxes:
            phase = (
                cb["phase"].replace("## 📅 ", "").strip() if cb["phase"] else "Unknown"
            )
            phase_progress[phase]["total"] += 1
            if cb["checked"]:
                phase_progress[phase]["completed"] += 1

        # Verify we have expected phases
        assert "PHASE 1: C++ FUNDAMENTALS" in phase_progress
        assert "PHASE 2: ADVANCED CONCEPTS" in phase_progress
        
        # Phase 1 should have some completion
        phase1 = phase_progress["PHASE 1: C++ FUNDAMENTALS"]
        assert phase1["total"] > 0
        assert phase1["completed"] > 0
        assert phase1["completed"] <= phase1["total"]
        
        # Phase 2 should have tasks but less/no completion
        phase2 = phase_progress["PHASE 2: ADVANCED CONCEPTS"]
        assert phase2["total"] > 0
        assert phase2["completed"] <= phase2["total"]

    def test_current_day_calculation(self, tracker_with_complex_data):
        """Test current day calculation logic"""
        tracker = tracker_with_complex_data
        
        current_day = tracker.get_current_day()
        
        # Should return the first day with uncompleted tasks
        uncompleted_days = []
        for cb in tracker.checkboxes:
            if not cb["checked"] and cb["day"] not in uncompleted_days:
                uncompleted_days.append(cb["day"])
        
        if uncompleted_days:
            expected_current = min(uncompleted_days)
            assert current_day == expected_current
        else:
            # All days completed
            assert current_day > max(cb["day"] for cb in tracker.checkboxes)

    def test_study_frequency_calculation(self, tracker_with_complex_data):
        """Test study frequency statistics"""
        tracker = tracker_with_complex_data
        
        # Add some history entries
        base_date = datetime.now() - timedelta(days=7)
        for i in range(5):  # 5 study sessions over 7 days
            tracker.progress_data["history"].append({
                "action": "complete",
                "day": i + 1,
                "timestamp": (base_date + timedelta(days=i)).isoformat()
            })
        
        tracker.progress_data["stats"]["total_study_sessions"] = 5
        
        # Calculate frequency like in show_stats()
        start_date = datetime.fromisoformat(tracker.progress_data["start_date"])
        days_since_start = max((datetime.now() - start_date).days + 1, 7)  # Ensure reasonable timeframe
        
        study_frequency = (
            (tracker.progress_data["stats"]["total_study_sessions"] / days_since_start * 100)
            if days_since_start > 0 else 0
        )
        
        assert 0 <= study_frequency <= 100
        assert study_frequency > 0  # Should have some activity

    def test_milestone_calculation(self, tracker_with_complex_data):
        """Test milestone progress calculation"""
        tracker = tracker_with_complex_data
        
        completed_days = len([cb for cb in tracker.checkboxes if cb["checked"]])
        
        # Test milestone logic
        milestones = {84: "Junior C++ Level", 168: "Course Completion"}
        
        next_milestone = None
        for day, desc in sorted(milestones.items()):
            if day > completed_days:
                next_milestone = (day, desc, day - completed_days)
                break
        
        if next_milestone:
            milestone_day, milestone_desc, days_away = next_milestone
            assert milestone_day > completed_days
            assert days_away > 0
            assert isinstance(milestone_desc, str)

    def test_empty_dataset_handling(self, temp_dir):
        """Test statistical calculations with empty datasets"""
        empty_markdown = """# Empty Study Plan

## 📅 PHASE 1: EMPTY

### Week 1
#### Day 1 (1 hour)
"""  # No checkboxes
        
        markdown_file = os.path.join(temp_dir, "empty.md")
        progress_file = os.path.join(temp_dir, ".empty_progress.json")
        
        with open(markdown_file, "w") as f:
            f.write(empty_markdown)
        
        tracker = StudyTracker(markdown_file, progress_file)
        tracker.parse_markdown()
        
        # Should handle empty data gracefully
        assert len(tracker.checkboxes) == 0
        assert tracker.get_current_day() == 1  # Default when no checkboxes
        
        # Progress calculations should not crash
        total_tasks = len(tracker.checkboxes)
        completed_tasks = len([cb for cb in tracker.checkboxes if cb["checked"]])
        percentage = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        
        assert percentage == 0

    def test_all_completed_dataset(self, temp_dir):
        """Test statistical calculations when everything is completed"""
        completed_markdown = """# Completed Study Plan

## 📅 PHASE 1: COMPLETE

### Week 1
#### Day 1 (1 hour)
- [x] Task 1
- [x] Task 2

#### Day 2 (1 hour)
- [x] Task 3
- [x] Mini Project: Complete Project
"""
        
        markdown_file = os.path.join(temp_dir, "completed.md")
        progress_file = os.path.join(temp_dir, ".completed_progress.json")
        
        with open(markdown_file, "w") as f:
            f.write(completed_markdown)
        
        tracker = StudyTracker(markdown_file, progress_file)
        tracker.parse_markdown()
        
        # All should be completed
        total_tasks = len(tracker.checkboxes)
        completed_tasks = len([cb for cb in tracker.checkboxes if cb["checked"]])
        
        assert total_tasks > 0
        assert completed_tasks == total_tasks
        
        percentage = (completed_tasks / total_tasks * 100)
        assert percentage == 100.0
        
        # Current day should be beyond all existing days
        max_day = max(cb["day"] for cb in tracker.checkboxes)
        current_day = tracker.get_current_day()
        assert current_day > max_day

    def test_large_dataset_performance(self, temp_dir):
        """Test statistical calculations with large datasets"""
        # Generate large markdown content
        large_markdown = "# Large Study Plan\n\n## 📅 PHASE 1: LARGE\n\n"
        
        for week in range(1, 21):  # 20 weeks
            large_markdown += f"### Week {week}\n"
            for day in range(1, 8):  # 7 days per week
                day_num = (week - 1) * 7 + day
                large_markdown += f"#### Day {day_num} (1 hour)\n"
                for task in range(1, 4):  # 3 tasks per day
                    status = "x" if day_num <= 50 else " "  # First 50 days completed
                    large_markdown += f"- [{status}] Task {task} for Day {day_num}\n"
                large_markdown += "\n"
        
        markdown_file = os.path.join(temp_dir, "large.md")
        progress_file = os.path.join(temp_dir, ".large_progress.json")
        
        with open(markdown_file, "w") as f:
            f.write(large_markdown)
        
        tracker = StudyTracker(markdown_file, progress_file)
        tracker.parse_markdown()
        
        # Should handle large datasets efficiently
        assert len(tracker.checkboxes) > 300  # 20 weeks * 7 days * 3 tasks
        
        # Calculations should complete without timeout
        total_tasks = len(tracker.checkboxes)
        completed_tasks = len([cb for cb in tracker.checkboxes if cb["checked"]])
        
        assert total_tasks > 0
        assert completed_tasks > 0
        assert completed_tasks < total_tasks  # Partial completion
        
        percentage = (completed_tasks / total_tasks * 100)
        assert 0 < percentage < 100

    def test_project_types_distinction(self, temp_dir):
        """Test proper distinction between project types"""
        project_markdown = """# Project Study Plan

## 📅 PHASE 1: PROJECTS

### Week 1
#### Day 1 (1 hour)
- [x] Mini Project: Calculator
- [x] Mini Project: Text Parser
- [x] Project: Web Scraper
- [x] Project: Database Manager
- [ ] Mini Project: Game Engine
- [ ] Project: Trading Bot
- [ ] Regular task without project
- [x] Another Mini Project: File Organizer
"""
        
        markdown_file = os.path.join(temp_dir, "projects.md")
        progress_file = os.path.join(temp_dir, ".projects_progress.json")
        
        with open(markdown_file, "w") as f:
            f.write(project_markdown)
        
        tracker = StudyTracker(markdown_file, progress_file)
        tracker.parse_markdown()
        
        # Count projects
        mini_projects_completed = 0
        major_projects_completed = 0
        
        for cb in tracker.checkboxes:
            if cb["checked"] and "Mini Project:" in cb["content"]:
                mini_projects_completed += 1
            elif (
                cb["checked"]
                and "Project:" in cb["content"]
                and "Mini" not in cb["content"]
            ):
                major_projects_completed += 1
        
        # Verify counts
        assert mini_projects_completed == 3  # Calculator, Text Parser, File Organizer
        assert major_projects_completed == 2  # Web Scraper, Database Manager
        
        # Count total projects (including uncompleted)
        total_mini = sum(1 for cb in tracker.checkboxes if "Mini Project:" in cb["content"])
        total_major = sum(1 for cb in tracker.checkboxes 
                         if "Project:" in cb["content"] and "Mini" not in cb["content"])
        
        assert total_mini == 4  # 3 completed + 1 pending
        assert total_major == 3  # 2 completed + 1 pending