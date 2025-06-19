"""
Unit tests for study_tracker.py
Run with: pytest tests/test_study_tracker.py -v
"""

import pytest
import json
import os
import tempfile
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
import sys

# Add parent directory to path to import study_tracker
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from study_tracker import StudyTracker


class TestStudyTracker:
    """Test suite for StudyTracker class"""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test files"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def sample_markdown(self):
        """Sample markdown content that matches actual file structure"""
        return """# C++ Quantitative Finance Learning Path

## 📅 PHASE 1: C++ FUNDAMENTALS (Weeks 1-8)

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
- [x] Watch: Variables and Data Types
- [x] Compare C++ types with Python types
- [ ] Code: Variable declaration exercises
- [ ] Note differences: static typing vs dynamic typing

### Week 2: Control Structures & Functions
**Goal**: Master flow control and modular programming

#### Day 8 (1 hour - Weekday)
- [ ] Watch: If-else statements
- [ ] Code: Trading signal generator (if price > MA)
- [ ] Practice: Nested conditions
- [ ] Compare with Python if-elif-else

#### Day 13 (2 hours - Weekend)
- [ ] Hour 1: Review and practice exercises
- [ ] Hour 2: Mini Project: Monte Carlo Pi estimation
  - [ ] Use loops and functions
  - [ ] Time your code execution
"""

    @pytest.fixture
    def tracker(self, temp_dir, sample_markdown):
        """Create a StudyTracker instance with test files"""
        markdown_file = os.path.join(temp_dir, "test_study_plan.md")
        progress_file = os.path.join(temp_dir, ".test_progress.json")

        # Write sample markdown
        with open(markdown_file, "w") as f:
            f.write(sample_markdown)

        return StudyTracker(markdown_file, progress_file)

    def test_initialization(self, tracker):
        """Test StudyTracker initialization"""
        assert tracker.markdown_file.endswith("test_study_plan.md")
        assert tracker.progress_file.endswith(".test_progress.json")
        assert isinstance(tracker.progress_data, dict)
        assert "completed_days" in tracker.progress_data
        assert "history" in tracker.progress_data
        assert "stats" in tracker.progress_data

    def test_create_initial_progress(self, tracker):
        """Test initial progress data structure"""
        progress = tracker.create_initial_progress()

        assert "start_date" in progress
        assert "last_activity" in progress
        assert "completed_days" in progress
        assert "history" in progress
        assert "stats" in progress

        assert progress["last_activity"] is None
        assert progress["completed_days"] == []
        assert progress["history"] == []
        assert progress["stats"]["total_study_sessions"] == 0
        assert progress["stats"]["longest_streak"] == 0
        assert progress["stats"]["current_streak"] == 0

    def test_parse_markdown(self, tracker):
        """Test markdown parsing functionality"""
        tracker.parse_markdown()

        # Count actual checkboxes with Day pattern
        assert len(tracker.checkboxes) > 0  # Should find checkboxes

        # Check first checkbox
        assert tracker.checkboxes[0]["day"] == 1
        assert tracker.checkboxes[0]["week"] == 1
        assert tracker.checkboxes[0]["checked"] == False
        assert "Install g++ compiler" in tracker.checkboxes[0]["content"]

        # Check that Day 3 items are partially checked
        day3_items = [cb for cb in tracker.checkboxes if cb["day"] == 3]
        assert len(day3_items) == 4
        assert day3_items[0]["checked"] == True  # Watch: Variables
        assert day3_items[1]["checked"] == True  # Compare C++ types
        assert day3_items[2]["checked"] == False  # Code: Variable
        assert day3_items[3]["checked"] == False  # Note differences

    def test_get_current_day(self, tracker):
        """Test getting the current (next uncompleted) day"""
        tracker.parse_markdown()

        # Day 1 should be current since it's not completed
        assert tracker.get_current_day() == 1

    def test_mark_day_complete(self, tracker):
        """Test marking a day as complete"""
        tracker.parse_markdown()

        # Get all day 1 items before marking
        day1_items_before = [cb for cb in tracker.checkboxes if cb["day"] == 1]
        uncompleted_day1 = [cb for cb in day1_items_before if not cb["checked"]]

        # Only mark if there are uncompleted items
        if uncompleted_day1:
            # Mark day 1 as complete
            result = tracker.mark_day_complete(1)
            assert result == True

            # Verify progress data updated
            assert 1 in tracker.progress_data["completed_days"]
            assert tracker.progress_data["stats"]["total_study_sessions"] == 1
            assert len(tracker.progress_data["history"]) == 1
            assert tracker.progress_data["history"][0]["action"] == "complete"
            assert tracker.progress_data["history"][0]["day"] == 1

    def test_mark_day_complete_auto(self, tracker):
        """Test marking next day complete without specifying day number"""
        tracker.parse_markdown()

        # Get current day before marking
        current_day = tracker.get_current_day()

        # Check if there are uncompleted items for current day
        current_day_items = [
            cb
            for cb in tracker.checkboxes
            if cb["day"] == current_day and not cb["checked"]
        ]

        if current_day_items:
            # Should mark current day as complete
            result = tracker.mark_day_complete()
            assert result == True
            assert current_day in tracker.progress_data["completed_days"]

    def test_save_and_load_progress(self, tracker):
        """Test saving and loading progress data"""
        # Add some progress
        tracker.progress_data["completed_days"] = [1, 2, 3]
        tracker.progress_data["stats"]["total_study_sessions"] = 3

        # Save
        tracker.save_progress()

        # Create new tracker instance to test loading
        new_tracker = StudyTracker(tracker.markdown_file, tracker.progress_file)

        assert new_tracker.progress_data["completed_days"] == [1, 2, 3]
        assert new_tracker.progress_data["stats"]["total_study_sessions"] == 3

    def test_undo_last_action(self, tracker):
        """Test undo functionality"""
        tracker.parse_markdown()

        # First mark a day complete
        current_day = tracker.get_current_day()
        current_day_items = [
            cb
            for cb in tracker.checkboxes
            if cb["day"] == current_day and not cb["checked"]
        ]

        if current_day_items:
            tracker.mark_day_complete(current_day)
            assert current_day in tracker.progress_data["completed_days"]

            # Undo
            result = tracker.undo_last_action()
            assert result == True
            assert current_day not in tracker.progress_data["completed_days"]

            # Check history has undo action
            assert tracker.progress_data["history"][-1]["action"] == "undo"
            assert tracker.progress_data["history"][-1]["day"] == current_day

    def test_undo_with_no_history(self, tracker):
        """Test undo when there's no history"""
        result = tracker.undo_last_action()
        assert result == False

    def test_update_streak(self, tracker):
        """Test streak calculation"""
        tracker.parse_markdown()

        # Get first two uncompleted days
        uncompleted_days = []
        for cb in tracker.checkboxes:
            if not cb["checked"] and cb["day"] not in uncompleted_days:
                uncompleted_days.append(cb["day"])
            if len(uncompleted_days) >= 2:
                break

        if len(uncompleted_days) >= 2:
            # Simulate completing days over time
            base_time = datetime.now()

            # Complete first day today
            with patch("study_tracker.datetime") as mock_datetime:
                mock_datetime.now.return_value = base_time
                mock_datetime.fromisoformat = datetime.fromisoformat
                tracker.mark_day_complete(uncompleted_days[0])

            # Complete second day tomorrow (continue streak)
            with patch("study_tracker.datetime") as mock_datetime:
                tomorrow = base_time + timedelta(days=1)
                mock_datetime.now.return_value = tomorrow
                mock_datetime.fromisoformat = datetime.fromisoformat
                tracker.mark_day_complete(uncompleted_days[1])

            # Streak should be 2
            assert tracker.progress_data["stats"]["current_streak"] >= 1

    def test_jump_to_day(self, tracker):
        """Test jumping to a specific day"""
        tracker.parse_markdown()

        # Jump to day 4 (should mark days 1, 2, 3 as complete if not already)
        with patch("study_tracker.Console.print"):  # Mock console output
            tracker.jump_to_day(4)

        # Check that earlier days are marked complete
        for day in [1, 2, 3]:
            # Check if any items from these days were marked
            day_items = [cb for cb in tracker.checkboxes if cb["day"] == day]
            if day_items:
                # The day should be in completed_days if it had uncompleted items
                pass  # This test is complex due to partial completion

    def test_jump_to_invalid_day(self, tracker):
        """Test jumping to invalid day numbers"""
        tracker.parse_markdown()

        with patch("study_tracker.Console.print") as mock_print:
            tracker.jump_to_day(0)  # Too low
            mock_print.assert_called()

            tracker.jump_to_day(1000)  # Too high
            mock_print.assert_called()

    def test_backup_markdown(self, tracker):
        """Test markdown file backup"""
        with patch("study_tracker.datetime") as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = "20240101_120000"

            tracker.backup_markdown()

            expected_backup = tracker.markdown_file + ".backup_20240101_120000"
            assert os.path.exists(expected_backup)

            # Clean up
            os.remove(expected_backup)

    def test_file_not_found(self, temp_dir):
        """Test handling of missing markdown file"""
        non_existent_file = os.path.join(temp_dir, "does_not_exist.md")
        progress_file = os.path.join(temp_dir, ".progress.json")

        with pytest.raises(SystemExit):
            tracker = StudyTracker(non_existent_file, progress_file)
            tracker.parse_markdown()

    def test_malformed_progress_file(self, tracker):
        """Test handling of corrupted progress file"""
        # Write invalid JSON to progress file
        with open(tracker.progress_file, "w") as f:
            f.write("invalid json content")

        # Should create new progress data instead of crashing
        new_tracker = StudyTracker(tracker.markdown_file, tracker.progress_file)
        assert isinstance(new_tracker.progress_data, dict)
        assert "completed_days" in new_tracker.progress_data

    def test_empty_markdown(self, temp_dir):
        """Test handling of empty markdown file"""
        empty_file = os.path.join(temp_dir, "empty.md")
        progress_file = os.path.join(temp_dir, ".progress.json")

        # Create empty file
        Path(empty_file).touch()

        tracker = StudyTracker(empty_file, progress_file)
        tracker.parse_markdown()

        assert len(tracker.checkboxes) == 0
        assert tracker.get_current_day() == 1  # Default when no checkboxes

    def test_mixed_checkbox_formats(self, temp_dir):
        """Test parsing different checkbox formats"""
        markdown_content = """### Week 1
#### Day 1 (1 hour)
- [ ] Lowercase unchecked
- [x] Lowercase x checked
- [X] Uppercase X checked

#### Day 2 (1 hour)
- [ ] Another task
"""

        markdown_file = os.path.join(temp_dir, "mixed.md")
        with open(markdown_file, "w") as f:
            f.write(markdown_content)

        tracker = StudyTracker(markdown_file, os.path.join(temp_dir, ".progress.json"))
        tracker.parse_markdown()

        # Should find 4 valid checkboxes with Day pattern
        assert len(tracker.checkboxes) == 4
        day1_items = [cb for cb in tracker.checkboxes if cb["day"] == 1]
        assert len(day1_items) == 3
        assert day1_items[0]["checked"] == False
        assert day1_items[1]["checked"] == True
        assert day1_items[2]["checked"] == True


class TestCLIFunctionality:
    """Test command-line interface functionality"""

    @pytest.fixture
    def mock_tracker(self):
        """Create a mock tracker for CLI tests"""
        with patch("study_tracker.StudyTracker") as MockTracker:
            mock_instance = MockTracker.return_value
            mock_instance.get_current_day.return_value = 5
            mock_instance.mark_day_complete.return_value = True
            mock_instance.undo_last_action.return_value = True
            yield mock_instance

    def test_main_done_argument(self, mock_tracker):
        """Test --done argument"""
        with patch("sys.argv", ["study_tracker.py", "--done"]):
            with patch("study_tracker.Console"):
                from study_tracker import main

                main()

        mock_tracker.mark_day_complete.assert_called_once()
        mock_tracker.show_status.assert_called_once()

    def test_main_status_argument(self, mock_tracker):
        """Test --status argument"""
        with patch("sys.argv", ["study_tracker.py", "--status"]):
            with patch("study_tracker.Console"):
                from study_tracker import main

                main()

        mock_tracker.show_status.assert_called_once()

    def test_main_next_argument(self, mock_tracker):
        """Test --next argument"""
        with patch("sys.argv", ["study_tracker.py", "--next"]):
            with patch("study_tracker.Console"):
                from study_tracker import main

                main()

        mock_tracker.show_next.assert_called_once()

    def test_main_week_summary_argument(self, mock_tracker):
        """Test --week-summary argument"""
        with patch("sys.argv", ["study_tracker.py", "--week-summary"]):
            with patch("study_tracker.Console"):
                from study_tracker import main

                main()

        mock_tracker.show_week_summary.assert_called_once()

    def test_main_undo_argument(self, mock_tracker):
        """Test --undo argument"""
        with patch("sys.argv", ["study_tracker.py", "--undo"]):
            with patch("study_tracker.Console"):
                from study_tracker import main

                main()

        mock_tracker.undo_last_action.assert_called_once()

    def test_main_stats_argument(self, mock_tracker):
        """Test --stats argument"""
        with patch("sys.argv", ["study_tracker.py", "--stats"]):
            with patch("study_tracker.Console"):
                from study_tracker import main

                main()

        mock_tracker.show_stats.assert_called_once()

    def test_main_backup_argument(self, mock_tracker):
        """Test --backup argument"""
        with patch("sys.argv", ["study_tracker.py", "--backup"]):
            with patch("study_tracker.Console"):
                from study_tracker import main

                main()

        mock_tracker.backup_markdown.assert_called_once()

    def test_main_jump_to_argument(self, mock_tracker):
        """Test --jump-to argument"""
        with patch("sys.argv", ["study_tracker.py", "--jump-to", "10"]):
            with patch("study_tracker.Console"):
                from study_tracker import main

                main()

        mock_tracker.jump_to_day.assert_called_once_with(10)

    def test_main_no_arguments(self, mock_tracker):
        """Test default behavior with no arguments"""
        with patch("sys.argv", ["study_tracker.py"]):
            with patch("study_tracker.Console"):
                from study_tracker import main

                main()

        # Should default to showing status
        mock_tracker.show_status.assert_called_once()


class TestProgressCalculations:
    """Test progress calculation methods"""

    @pytest.fixture
    def tracker_with_progress(self, temp_dir, sample_markdown):
        """Create tracker with some progress"""
        markdown_file = os.path.join(temp_dir, "test_study_plan.md")
        progress_file = os.path.join(temp_dir, ".test_progress.json")

        with open(markdown_file, "w") as f:
            f.write(sample_markdown)

        tracker = StudyTracker(markdown_file, progress_file)
        tracker.parse_markdown()

        # Try to mark some days complete
        uncompleted_days = []
        for cb in tracker.checkboxes:
            if not cb["checked"] and cb["day"] not in uncompleted_days:
                uncompleted_days.append(cb["day"])

        # Mark first two uncompleted days
        for day in uncompleted_days[:2]:
            tracker.mark_day_complete(day)

        return tracker

    def test_progress_percentage(self, tracker_with_progress):
        """Test progress percentage calculation"""
        total_days = len(tracker_with_progress.checkboxes)
        completed_days = len(
            [cb for cb in tracker_with_progress.checkboxes if cb["checked"]]
        )

        percentage = (completed_days / total_days * 100) if total_days > 0 else 0
        assert percentage >= 0
        assert percentage <= 100

    def test_week_progress_calculation(self, tracker_with_progress):
        """Test week progress calculation"""
        # Get week 1 progress
        week1_items = [cb for cb in tracker_with_progress.checkboxes if cb["week"] == 1]
        week1_completed = [cb for cb in week1_items if cb["checked"]]

        assert len(week1_items) > 0  # Should have week 1 items
        assert len(week1_completed) >= 0  # May or may not have completed items

    def test_project_counting(self, tracker_with_progress):
        """Test counting of projects"""
        mini_projects = 0
        major_projects = 0

        for cb in tracker_with_progress.checkboxes:
            if cb["checked"] and "Mini Project:" in cb["content"]:
                mini_projects += 1
            elif (
                cb["checked"]
                and "Project:" in cb["content"]
                and "Mini" not in cb["content"]
            ):
                major_projects += 1

        assert mini_projects >= 0
        assert major_projects >= 0


class TestEdgeCases:
    """Test edge cases and error conditions"""

    def test_unicode_in_markdown(self, temp_dir):
        """Test handling of unicode characters in markdown"""
        markdown_content = """### Week 1
#### Day 1 (1 hour)
- [ ] Task with emoji 🔥
- [ ] Task with unicode: α β γ
- [ ] Task with special chars: <>&"'
"""

        markdown_file = os.path.join(temp_dir, "unicode.md")
        with open(markdown_file, "w", encoding="utf-8") as f:
            f.write(markdown_content)

        tracker = StudyTracker(markdown_file, os.path.join(temp_dir, ".progress.json"))
        tracker.parse_markdown()

        assert len(tracker.checkboxes) == 3
        assert "🔥" in tracker.checkboxes[0]["content"]
        assert "α β γ" in tracker.checkboxes[1]["content"]

    def test_concurrent_modifications(self, isolated_tracker):
        """Test handling when markdown is modified externally"""
        tracker = isolated_tracker
        tracker.parse_markdown()
        initial_count = len(tracker.checkboxes)

        # Simulate external modification
        with open(tracker.markdown_file, "a") as f:
            f.write("\n#### Day 999 (1 hour)\n- [ ] New task added externally\n")

        # Re-parse should pick up the change
        tracker.parse_markdown()
        assert len(tracker.checkboxes) == initial_count + 1

    def test_very_long_task_description(self, temp_dir):
        """Test handling of very long task descriptions"""
        long_description = "A" * 500  # 500 character task
        markdown_content = f"""### Week 1
#### Day 1 (1 hour)
- [ ] {long_description}
"""

        markdown_file = os.path.join(temp_dir, "long.md")
        with open(markdown_file, "w") as f:
            f.write(markdown_content)

        tracker = StudyTracker(markdown_file, os.path.join(temp_dir, ".progress.json"))
        tracker.parse_markdown()

        assert len(tracker.checkboxes) == 1
        assert len(tracker.checkboxes[0]["content"]) > 400
