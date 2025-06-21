"""
Unit tests for error handling in study_tracker.py
Tests critical error scenarios and edge cases
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
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


class TestErrorHandling:
    """Test error handling scenarios"""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test files"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def sample_markdown(self):
        """Sample markdown content for testing"""
        return """# Test Study Plan

## 📅 PHASE 1: FUNDAMENTALS

### Week 1
#### Day 1 (1 hour)
- [ ] Task 1
- [ ] Task 2

#### Day 2 (1 hour)
- [ ] Task 3
- [ ] Task 4
"""

    def test_missing_rich_dependency(self):
        """Test graceful handling when rich library is missing"""
        # Mock sys.modules to simulate missing rich
        with patch.dict('sys.modules', {'rich': None, 'rich.console': None, 
                                       'rich.table': None, 'rich.progress': None,
                                       'rich.panel': None, 'rich.text': None}):
            with patch('builtins.print') as mock_print:
                with pytest.raises(SystemExit) as exc_info:
                    # Force reimport to trigger ImportError
                    if 'study_tracker' in sys.modules:
                        del sys.modules['study_tracker']
                    import study_tracker
                
                assert exc_info.value.code == 1
                mock_print.assert_called_with("Please install 'rich' library: pip install rich")

    def test_mark_day_complete_no_checkboxes(self, temp_dir, sample_markdown):
        """Test marking complete when no checkboxes exist for day"""
        from study_tracker import StudyTracker
        
        markdown_file = os.path.join(temp_dir, "test.md")
        progress_file = os.path.join(temp_dir, ".progress.json")
        
        with open(markdown_file, "w") as f:
            f.write(sample_markdown)
        
        tracker = StudyTracker(markdown_file, progress_file)
        tracker.parse_markdown()
        
        # Try to mark a non-existent day
        result = tracker.mark_day_complete(999)
        assert result == False
        
        # Try to mark an already completed day (should return False if no unchecked items)
        tracker.mark_day_complete(1)  # Complete day 1 first
        result = tracker.mark_day_complete(1)  # Try to complete again
        assert result == False

    def test_undo_with_no_complete_actions(self, temp_dir, sample_markdown):
        """Test undo when history has no complete actions"""
        from study_tracker import StudyTracker
        
        markdown_file = os.path.join(temp_dir, "test.md")
        progress_file = os.path.join(temp_dir, ".progress.json")
        
        with open(markdown_file, "w") as f:
            f.write(sample_markdown)
        
        tracker = StudyTracker(markdown_file, progress_file)
        
        # Add non-complete actions to history
        tracker.progress_data["history"] = [
            {"action": "other", "day": 1, "timestamp": "2024-01-01T00:00:00"}
        ]
        
        result = tracker.undo_last_action()
        assert result == False

    def test_undo_last_action_no_checkboxes(self, temp_dir, sample_markdown):
        """Test undo when no checkboxes exist for the last completed day"""
        from study_tracker import StudyTracker
        
        markdown_file = os.path.join(temp_dir, "test.md")
        progress_file = os.path.join(temp_dir, ".progress.json")
        
        with open(markdown_file, "w") as f:
            f.write(sample_markdown)
        
        tracker = StudyTracker(markdown_file, progress_file)
        tracker.parse_markdown()
        
        # Add a complete action for a day that has no checked boxes
        tracker.progress_data["history"] = [
            {"action": "complete", "day": 999, "timestamp": "2024-01-01T00:00:00"}
        ]
        
        result = tracker.undo_last_action()
        assert result == False

    def test_backup_permission_error(self, temp_dir, sample_markdown):
        """Test backup handling when file permissions prevent copy"""
        from study_tracker import StudyTracker
        
        markdown_file = os.path.join(temp_dir, "test.md")
        progress_file = os.path.join(temp_dir, ".progress.json")
        
        with open(markdown_file, "w") as f:
            f.write(sample_markdown)
        
        tracker = StudyTracker(markdown_file, progress_file)
        
        with patch('shutil.copy2', side_effect=PermissionError("Access denied")):
            with patch('study_tracker.console.print') as mock_print:
                tracker.backup_markdown()
                mock_print.assert_called_with("[red]Error creating backup: Access denied[/red]")

    def test_backup_general_error(self, temp_dir, sample_markdown):
        """Test backup handling for general exceptions"""
        from study_tracker import StudyTracker
        
        markdown_file = os.path.join(temp_dir, "test.md")
        progress_file = os.path.join(temp_dir, ".progress.json")
        
        with open(markdown_file, "w") as f:
            f.write(sample_markdown)
        
        tracker = StudyTracker(markdown_file, progress_file)
        
        with patch('shutil.copy2', side_effect=OSError("Disk full")):
            with patch('study_tracker.console.print') as mock_print:
                tracker.backup_markdown()
                mock_print.assert_called_with("[red]Error creating backup: Disk full[/red]")

    def test_save_progress_write_error(self, temp_dir, sample_markdown):
        """Test progress saving when write fails"""
        from study_tracker import StudyTracker
        
        markdown_file = os.path.join(temp_dir, "test.md")
        progress_file = os.path.join(temp_dir, ".progress.json")
        
        with open(markdown_file, "w") as f:
            f.write(sample_markdown)
        
        tracker = StudyTracker(markdown_file, progress_file)
        
        with patch('builtins.open', side_effect=OSError("No space left on device")):
            with pytest.raises(OSError):
                tracker.save_progress()

    def test_parse_markdown_file_not_found(self, temp_dir):
        """Test handling of missing markdown file"""
        from study_tracker import StudyTracker
        
        non_existent_file = os.path.join(temp_dir, "does_not_exist.md")
        progress_file = os.path.join(temp_dir, ".progress.json")
        
        tracker = StudyTracker(non_existent_file, progress_file)
        
        with patch('study_tracker.console.print') as mock_print:
            with pytest.raises(SystemExit):
                tracker.parse_markdown()
            mock_print.assert_called_with(f"[red]Error: {non_existent_file} not found![/red]")

    def test_load_progress_malformed_json(self, temp_dir, sample_markdown):
        """Test handling of corrupted progress file"""
        from study_tracker import StudyTracker
        
        markdown_file = os.path.join(temp_dir, "test.md")
        progress_file = os.path.join(temp_dir, ".progress.json")
        
        with open(markdown_file, "w") as f:
            f.write(sample_markdown)
        
        # Write invalid JSON to progress file
        with open(progress_file, "w") as f:
            f.write("invalid json content")
        
        # Should create new progress data instead of crashing
        tracker = StudyTracker(markdown_file, progress_file)
        assert isinstance(tracker.progress_data, dict)
        assert "completed_days" in tracker.progress_data
        assert tracker.progress_data["completed_days"] == []

    def test_jump_to_invalid_day_numbers(self, temp_dir, sample_markdown):
        """Test jumping to invalid day numbers"""
        from study_tracker import StudyTracker
        
        markdown_file = os.path.join(temp_dir, "test.md")
        progress_file = os.path.join(temp_dir, ".progress.json")
        
        with open(markdown_file, "w") as f:
            f.write(sample_markdown)
        
        tracker = StudyTracker(markdown_file, progress_file)
        tracker.parse_markdown()
        
        total_days = len(tracker.checkboxes)
        
        with patch('study_tracker.console.print') as mock_print:
            # Test day too low
            tracker.jump_to_day(0)
            mock_print.assert_called_with(
                f"[red]Invalid day number. Must be between 1 and {total_days}[/red]"
            )
            
            # Test day too high
            tracker.jump_to_day(1000)
            mock_print.assert_called_with(
                f"[red]Invalid day number. Must be between 1 and {total_days}[/red]"
            )

    def test_update_streak_empty_history(self, temp_dir, sample_markdown):
        """Test streak update with empty history"""
        from study_tracker import StudyTracker
        
        markdown_file = os.path.join(temp_dir, "test.md")
        progress_file = os.path.join(temp_dir, ".progress.json")
        
        with open(markdown_file, "w") as f:
            f.write(sample_markdown)
        
        tracker = StudyTracker(markdown_file, progress_file)
        tracker.progress_data["history"] = []
        
        # Should not crash with empty history
        tracker.update_streak()
        assert tracker.progress_data["stats"]["current_streak"] == 0

    def test_main_function_error_handling(self, temp_dir, sample_markdown):
        """Test main function error handling for failed operations"""
        from study_tracker import StudyTracker, main
        
        markdown_file = os.path.join(temp_dir, "test.md")
        progress_file = os.path.join(temp_dir, ".progress.json")
        
        with open(markdown_file, "w") as f:
            f.write(sample_markdown)
        
        # Test failed day completion
        with patch('sys.argv', ['study_tracker.py', '--done']):
            with patch('study_tracker.StudyTracker') as MockTracker:
                mock_instance = MockTracker.return_value
                mock_instance.get_current_day.return_value = 1
                mock_instance.mark_day_complete.return_value = False  # Simulate failure
                
                with patch('study_tracker.console.print') as mock_print:
                    main()
                    mock_print.assert_called_with("[red]Failed to mark day as complete[/red]")
        
        # Test failed undo
        with patch('sys.argv', ['study_tracker.py', '--undo']):
            with patch('study_tracker.StudyTracker') as MockTracker:
                mock_instance = MockTracker.return_value
                mock_instance.undo_last_action.return_value = False  # Simulate failure
                
                with patch('study_tracker.console.print') as mock_print:
                    main()
                    mock_print.assert_called_with("[red]No action to undo[/red]")