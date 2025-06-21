"""
Integration tests for study_tracker.py workflows
Tests complete user workflows and data consistency across operations
"""

import pytest
import json
import os
import tempfile
import shutil
import copy
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys

# Add parent directory to path to import study_tracker
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from study_tracker import StudyTracker


class TestWorkflowIntegration:
    """Test complete user workflows and data consistency"""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test files"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def workflow_markdown(self):
        """Realistic markdown content for workflow testing"""
        return """# C++ Quantitative Finance Learning Path

## 📅 PHASE 1: C++ FUNDAMENTALS (Weeks 1-4)

### Week 1: Setup & C++ Basics
**Goal**: Environment setup and basic syntax

#### Day 1 (1 hour - Weekday)
- [ ] Install g++ compiler and VS Code C++ extensions
- [ ] Configure VS Code for C++ development
- [ ] Create GitHub repo: "cpp-quant-journey"
- [ ] Watch Course 1: Introduction & Course Overview

#### Day 2 (1 hour - Weekday)
- [ ] Watch: C++ Basics - Program Structure
- [ ] Code: First "Hello World" program
- [ ] Understand compilation process (vs Python interpretation)
- [ ] Practice: Compile and run from terminal

#### Day 3 (1 hour - Weekday)
- [ ] Watch: Variables and Data Types
- [ ] Compare C++ types with Python types
- [ ] Code: Variable declaration exercises
- [ ] Note differences: static typing vs dynamic typing

#### Day 4 (1 hour - Weekday)
- [ ] Watch: Input/Output in C++
- [ ] Code: Interactive program with user input
- [ ] Practice: cin, cout, and formatting

#### Day 5 (2 hours - Weekend)
- [ ] Hour 1: Control structures - if/else statements
- [ ] Hour 2: Mini Project: Simple decision-making program
- [ ] Test: Calculator with basic operations (+, -, *, /)

### Week 2: Control Structures & Functions
**Goal**: Master flow control and modular programming

#### Day 6 (1 hour - Weekday)
- [ ] Watch: Loops - for, while, do-while
- [ ] Code: Number guessing game using loops
- [ ] Practice: Break and continue statements

#### Day 7 (1 hour - Weekday)
- [ ] Watch: Functions - declaration, definition, parameters
- [ ] Code: Function examples with return values
- [ ] Practice: Function overloading basics

#### Day 8 (1 hour - Weekday)
- [ ] Watch: Arrays and basic string handling
- [ ] Code: Array manipulation exercises
- [ ] Practice: Multi-dimensional arrays

#### Day 9 (1 hour - Weekday)
- [ ] Watch: Pointers and references introduction
- [ ] Code: Basic pointer operations
- [ ] Practice: Pointer arithmetic

#### Day 10 (2 hours - Weekend)
- [ ] Hour 1: Review and practice exercises
- [ ] Hour 2: Project: Monte Carlo Pi estimation
- [ ] Implement: Random number generation and statistics
"""

    @pytest.fixture
    def tracker(self, temp_dir, workflow_markdown):
        """Create a StudyTracker instance for workflow testing"""
        markdown_file = os.path.join(temp_dir, "workflow_study_plan.md")
        progress_file = os.path.join(temp_dir, ".workflow_progress.json")

        with open(markdown_file, "w") as f:
            f.write(workflow_markdown)

        return StudyTracker(markdown_file, progress_file)

    def test_complete_study_session_workflow(self, tracker):
        """Test complete workflow: check status → mark complete → show next"""
        tracker.parse_markdown()

        # Initial state
        initial_day = tracker.get_current_day()
        initial_completed = len(tracker.progress_data["completed_days"])
        initial_sessions = tracker.progress_data["stats"]["total_study_sessions"]

        # Check that we have a valid starting state
        assert initial_day >= 1
        assert len(tracker.checkboxes) > 0

        # Mark day complete
        success = tracker.mark_day_complete()
        assert success == True

        # Verify state changes
        new_day = tracker.get_current_day()
        new_completed = len(tracker.progress_data["completed_days"])
        new_sessions = tracker.progress_data["stats"]["total_study_sessions"]

        # Day should advance only if we completed all tasks for that day
        day_tasks = [cb for cb in tracker.checkboxes if cb["day"] == initial_day]
        all_completed = all(cb["checked"] for cb in day_tasks)
        
        if all_completed:
            assert new_day > initial_day
        else:
            assert new_day == initial_day

        # Progress tracking should update
        assert new_completed >= initial_completed
        assert new_sessions == initial_sessions + 1

        # Verify history recorded
        assert len(tracker.progress_data["history"]) >= 1
        last_entry = tracker.progress_data["history"][-1]
        assert last_entry["action"] == "complete"
        assert last_entry["day"] == initial_day

    def test_undo_redo_consistency(self, tracker):
        """Test data consistency through undo/redo operations"""
        tracker.parse_markdown()
        
        # Capture initial state
        initial_state = {
            "completed_days": copy.deepcopy(tracker.progress_data["completed_days"]),
            "total_sessions": tracker.progress_data["stats"]["total_study_sessions"],
            "checkboxes": copy.deepcopy([(cb["day"], cb["checked"]) for cb in tracker.checkboxes])
        }

        # Perform operation
        initial_day = tracker.get_current_day()
        tracker.mark_day_complete(initial_day)
        
        # Note: modified_state would be captured here for comparison if needed

        # Undo operation
        undo_success = tracker.undo_last_action()
        assert undo_success == True

        # Verify state restoration
        final_state = {
            "completed_days": copy.deepcopy(tracker.progress_data["completed_days"]),
            "total_sessions": tracker.progress_data["stats"]["total_study_sessions"],  # Should remain same
            "checkboxes": copy.deepcopy([(cb["day"], cb["checked"]) for cb in tracker.checkboxes])
        }

        # Completed days should be restored
        assert final_state["completed_days"] == initial_state["completed_days"]
        
        # Checkbox states should be restored
        assert final_state["checkboxes"] == initial_state["checkboxes"]

        # History should record both operations
        assert len(tracker.progress_data["history"]) >= 2
        assert tracker.progress_data["history"][-2]["action"] == "complete"
        assert tracker.progress_data["history"][-1]["action"] == "undo"

    def test_jump_to_day_bulk_completion(self, tracker):
        """Test jumping to a day marks all previous days as complete"""
        tracker.parse_markdown()

        # Jump to day 3 (should complete days 1 and 2)
        target_day = 3
        initial_completed = len(tracker.progress_data["completed_days"])

        with patch('study_tracker.console.print'):  # Suppress output
            tracker.jump_to_day(target_day)

        # Verify bulk completion
        new_completed = len(tracker.progress_data["completed_days"])
        assert new_completed >= initial_completed

        # Check that days 1 and 2 are marked complete
        for day in range(1, target_day):
            day_tasks = [cb for cb in tracker.checkboxes if cb["day"] == day]
            if day_tasks:  # Only check if day has tasks
                # At least some tasks for this day should be completed
                completed_tasks = [cb for cb in day_tasks if cb["checked"]]
                assert len(completed_tasks) > 0

        # Verify current day is now target day or beyond
        current_day = tracker.get_current_day()
        assert current_day >= target_day

    def test_multi_day_completion_sequence(self, tracker):
        """Test completing multiple days in sequence"""
        tracker.parse_markdown()

        days_to_complete = 3
        completed_days = []

        # Complete multiple days in sequence
        for i in range(days_to_complete):
            current_day = tracker.get_current_day()
            success = tracker.mark_day_complete()
            
            if success:
                completed_days.append(current_day)
                
                # Verify immediate state
                assert current_day in tracker.progress_data["completed_days"]
                
                # Check that day's tasks are marked complete
                day_tasks = [cb for cb in tracker.checkboxes if cb["day"] == current_day]
                completed_tasks = [cb for cb in day_tasks if cb["checked"]]
                assert len(completed_tasks) > 0

        # Verify overall progress
        assert len(completed_days) <= days_to_complete
        assert tracker.progress_data["stats"]["total_study_sessions"] == len(completed_days)

        # Verify history integrity
        complete_actions = [entry for entry in tracker.progress_data["history"] 
                          if entry["action"] == "complete"]
        assert len(complete_actions) == len(completed_days)

    def test_backup_restore_workflow(self, tracker):
        """Test backup creation and file integrity"""
        tracker.parse_markdown()

        # Create initial backup
        with patch('study_tracker.datetime') as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = "20240101_120000"
            with patch('study_tracker.console.print'):
                tracker.backup_markdown()

        expected_backup = tracker.markdown_file + ".backup_20240101_120000"
        assert os.path.exists(expected_backup)

        # Modify original file
        tracker.mark_day_complete(1)
        tracker.save_markdown()

        # Verify backup is different from modified file
        with open(tracker.markdown_file, 'r') as f:
            modified_content = f.read()
        
        with open(expected_backup, 'r') as f:
            backup_content = f.read()

        assert modified_content != backup_content
        assert "- [x]" in modified_content  # Should have completed checkboxes
        assert "- [ ]" in backup_content    # Backup should have original unchecked

        # Clean up
        os.remove(expected_backup)

    def test_streak_across_multiple_sessions(self, tracker):
        """Test streak calculation across multiple study sessions"""
        tracker.parse_markdown()

        base_date = datetime.now() - timedelta(days=5)
        completed_days = []

        # Simulate study sessions over consecutive days
        for i in range(4):  # 4 consecutive days
            study_date = base_date + timedelta(days=i)
            
            with patch('study_tracker.datetime') as mock_datetime:
                mock_datetime.now.return_value = study_date
                mock_datetime.fromisoformat = datetime.fromisoformat
                
                success = tracker.mark_day_complete(i + 1)
                if success:
                    completed_days.append(i + 1)

        # Verify streak calculation
        final_streak = tracker.progress_data["stats"]["current_streak"]
        longest_streak = tracker.progress_data["stats"]["longest_streak"]

        # Should have some streak (depends on whether last day was recent enough)
        assert longest_streak >= 2  # Should build some streak
        assert longest_streak >= final_streak

        # Verify all days were completed
        assert len(completed_days) == 4
        for day in completed_days:
            assert day in tracker.progress_data["completed_days"]

    def test_concurrent_file_access_simulation(self, tracker):
        """Test handling of concurrent file modifications"""
        tracker.parse_markdown()
        initial_checkboxes = len(tracker.checkboxes)

        # Simulate external modification of markdown file
        external_content = "\n#### Day 999 (1 hour)\n- [ ] External task added\n"
        with open(tracker.markdown_file, "a") as f:
            f.write(external_content)

        # Re-parse should pick up the change
        tracker.parse_markdown()
        new_checkboxes = len(tracker.checkboxes)

        assert new_checkboxes == initial_checkboxes + 1

        # Operations should still work correctly
        success = tracker.mark_day_complete(999)
        assert success == True

    def test_large_session_workflow(self, tracker):
        """Test workflow with extended study session"""
        tracker.parse_markdown()

        # Simulate a long study session completing multiple days
        session_start = datetime.now()
        days_completed = 0
        max_days = 5

        for attempt in range(max_days):
            current_day = tracker.get_current_day()
            
            # Check if we can complete more days
            day_tasks = [cb for cb in tracker.checkboxes if cb["day"] == current_day]
            if not day_tasks:
                break
                
            with patch('study_tracker.datetime') as mock_datetime:
                session_time = session_start + timedelta(hours=attempt)
                mock_datetime.now.return_value = session_time
                mock_datetime.fromisoformat = datetime.fromisoformat
                
                success = tracker.mark_day_complete()
                if success:
                    days_completed += 1
                else:
                    break

        # Verify session results
        assert days_completed > 0
        assert tracker.progress_data["stats"]["total_study_sessions"] == days_completed

        # All completed days should be in tracking
        for i in range(1, days_completed + 1):
            assert i in tracker.progress_data["completed_days"]

    def test_data_persistence_across_instances(self, tracker):
        """Test data persistence when creating new tracker instances"""
        tracker.parse_markdown()

        # Complete some work
        tracker.mark_day_complete(1)
        tracker.mark_day_complete(2)
        
        # Capture state
        original_completed = copy.deepcopy(tracker.progress_data["completed_days"])
        original_sessions = tracker.progress_data["stats"]["total_study_sessions"]

        # Create new instance (simulates app restart)
        new_tracker = StudyTracker(tracker.markdown_file, tracker.progress_file)
        
        # Verify persistence
        assert new_tracker.progress_data["completed_days"] == original_completed
        assert new_tracker.progress_data["stats"]["total_study_sessions"] == original_sessions

        # New operations should build on existing data
        new_tracker.parse_markdown()
        success = new_tracker.mark_day_complete(3)
        
        if success:
            assert len(new_tracker.progress_data["completed_days"]) >= len(original_completed)
            assert new_tracker.progress_data["stats"]["total_study_sessions"] >= original_sessions

    def test_error_recovery_workflow(self, tracker):
        """Test workflow recovery from error conditions"""
        tracker.parse_markdown()

        # Create a scenario with file permission issues
        
        # Simulate file write failure
        with patch('builtins.open', side_effect=OSError("Permission denied")):
            try:
                tracker.mark_day_complete(1)
            except OSError:
                pass  # Expected failure

        # Data should remain consistent despite write failure
        # (Note: actual implementation might handle this differently)
        
        # Create new instance to test recovery
        recovery_tracker = StudyTracker(tracker.markdown_file, tracker.progress_file)
        
        # Should be able to continue operations
        recovery_tracker.parse_markdown()
        success = recovery_tracker.mark_day_complete(1)
        
        # Recovery should work
        assert isinstance(success, bool)  # Should not crash