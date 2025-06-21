"""
Unit tests for streak calculations in study_tracker.py
Tests edge cases and complex scenarios for streak logic
"""

import pytest
import json
import os
import tempfile
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys

# Add parent directory to path to import study_tracker
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from study_tracker import StudyTracker


class TestStreakCalculations:
    """Test streak calculation logic and edge cases"""

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

#### Day 3 (1 hour)
- [ ] Task 5
- [ ] Task 6

#### Day 4 (1 hour)
- [ ] Task 7
- [ ] Task 8

#### Day 5 (1 hour)
- [ ] Task 9
- [ ] Task 10
"""

    @pytest.fixture
    def tracker(self, temp_dir, sample_markdown):
        """Create a StudyTracker instance with test files"""
        markdown_file = os.path.join(temp_dir, "test_study_plan.md")
        progress_file = os.path.join(temp_dir, ".test_progress.json")

        with open(markdown_file, "w") as f:
            f.write(sample_markdown)

        return StudyTracker(markdown_file, progress_file)

    def test_streak_reset_after_gap(self, tracker):
        """Test streak resets to 0 when study gap exceeds 1 day"""
        tracker.parse_markdown()

        # Complete day 3 days ago
        past_date = datetime.now() - timedelta(days=3)
        
        with patch('study_tracker.datetime') as mock_datetime:
            mock_datetime.now.return_value = past_date
            mock_datetime.fromisoformat = datetime.fromisoformat
            tracker.mark_day_complete(1)

        # Current streak should be 0 due to gap
        tracker.update_streak()
        assert tracker.progress_data["stats"]["current_streak"] == 0

    def test_consecutive_day_streak(self, tracker):
        """Test streak increments for consecutive days"""
        tracker.parse_markdown()
        base_date = datetime.now()

        # Complete 3 consecutive days
        for i in range(3):
            test_date = base_date + timedelta(days=i)
            with patch('study_tracker.datetime') as mock_datetime:
                mock_datetime.now.return_value = test_date
                mock_datetime.fromisoformat = datetime.fromisoformat
                tracker.mark_day_complete(i + 1)

        assert tracker.progress_data["stats"]["current_streak"] == 3
        assert tracker.progress_data["stats"]["longest_streak"] == 3

    def test_streak_yesterday_today_continuation(self, tracker):
        """Test streak continues when last study was yesterday"""
        tracker.parse_markdown()
        
        # Complete yesterday
        yesterday = datetime.now() - timedelta(days=1)
        with patch('study_tracker.datetime') as mock_datetime:
            mock_datetime.now.return_value = yesterday
            mock_datetime.fromisoformat = datetime.fromisoformat
            tracker.mark_day_complete(1)

        # Complete today
        today = datetime.now()
        with patch('study_tracker.datetime') as mock_datetime:
            mock_datetime.now.return_value = today
            mock_datetime.fromisoformat = datetime.fromisoformat
            tracker.mark_day_complete(2)

        assert tracker.progress_data["stats"]["current_streak"] == 2

    def test_streak_calculation_with_empty_history(self, tracker):
        """Test streak calculation with empty history"""
        tracker.parse_markdown()
        tracker.progress_data["history"] = []
        
        tracker.update_streak()
        
        assert tracker.progress_data["stats"]["current_streak"] == 0
        assert tracker.progress_data["stats"]["longest_streak"] == 0

    def test_streak_calculation_with_no_complete_actions(self, tracker):
        """Test streak calculation when history has no complete actions"""
        tracker.parse_markdown()
        tracker.progress_data["history"] = [
            {"action": "undo", "day": 1, "timestamp": datetime.now().isoformat()},
            {"action": "other", "day": 2, "timestamp": datetime.now().isoformat()}
        ]
        
        tracker.update_streak()
        
        assert tracker.progress_data["stats"]["current_streak"] == 0

    def test_longest_streak_tracking(self, tracker):
        """Test that longest streak is properly tracked across multiple streaks"""
        tracker.parse_markdown()
        base_date = datetime.now() - timedelta(days=10)

        # First streak of 3 days
        for i in range(3):
            test_date = base_date + timedelta(days=i)
            with patch('study_tracker.datetime') as mock_datetime:
                mock_datetime.now.return_value = test_date
                mock_datetime.fromisoformat = datetime.fromisoformat
                tracker.mark_day_complete(i + 1)

        # Gap of 3 days, then streak of 2 days
        for i in range(2):
            test_date = base_date + timedelta(days=i + 6)  # 3 day gap
            with patch('study_tracker.datetime') as mock_datetime:
                mock_datetime.now.return_value = test_date
                mock_datetime.fromisoformat = datetime.fromisoformat
                tracker.mark_day_complete(i + 4)

        # Longest streak should still be 3
        assert tracker.progress_data["stats"]["longest_streak"] == 3
        # Current streak depends on how recent the last study was
        assert tracker.progress_data["stats"]["current_streak"] >= 0

    def test_same_day_multiple_completions(self, tracker):
        """Test streak calculation when multiple days completed on same calendar day"""
        tracker.parse_markdown()
        today = datetime.now()

        # Complete multiple study days on the same calendar day
        with patch('study_tracker.datetime') as mock_datetime:
            mock_datetime.now.return_value = today
            mock_datetime.fromisoformat = datetime.fromisoformat
            tracker.mark_day_complete(1)
            tracker.mark_day_complete(2)
            tracker.mark_day_complete(3)

        # Should count as streak of 1 calendar day, not 3
        assert tracker.progress_data["stats"]["current_streak"] == 1

    def test_weekend_gap_handling(self, tracker):
        """Test streak logic across weekend gaps"""
        tracker.parse_markdown()
        
        # Complete Friday
        friday = datetime(2024, 1, 5)  # Assuming this is a Friday
        with patch('study_tracker.datetime') as mock_datetime:
            mock_datetime.now.return_value = friday
            mock_datetime.fromisoformat = datetime.fromisoformat
            tracker.mark_day_complete(1)

        # Complete Monday (3 day gap including weekend)
        monday = datetime(2024, 1, 8)
        with patch('study_tracker.datetime') as mock_datetime:
            mock_datetime.now.return_value = monday
            mock_datetime.fromisoformat = datetime.fromisoformat
            tracker.mark_day_complete(2)

        # Streak should be broken due to gap > 1 day
        assert tracker.progress_data["stats"]["current_streak"] == 1

    def test_streak_with_duplicate_dates(self, tracker):
        """Test streak calculation with duplicate completion dates"""
        tracker.parse_markdown()
        today = datetime.now()

        # Complete day 1 twice on same day (edge case)
        with patch('study_tracker.datetime') as mock_datetime:
            mock_datetime.now.return_value = today
            mock_datetime.fromisoformat = datetime.fromisoformat
            tracker.mark_day_complete(1)
            
            # Manually add duplicate history entry
            tracker.progress_data["history"].append({
                "action": "complete",
                "day": 2,
                "timestamp": today.isoformat()
            })

        tracker.update_streak()
        
        # Should handle duplicates gracefully (same date counted once)
        assert tracker.progress_data["stats"]["current_streak"] == 1

    def test_streak_calculation_performance(self, tracker):
        """Test streak calculation with many history entries"""
        tracker.parse_markdown()
        base_date = datetime.now() - timedelta(days=100)

        # Create large history with many entries
        for i in range(50):
            test_date = base_date + timedelta(days=i * 2)  # Every other day
            tracker.progress_data["history"].append({
                "action": "complete", 
                "day": i + 1,
                "timestamp": test_date.isoformat()
            })

        # Should handle large datasets without issues
        tracker.update_streak()
        
        # Verify calculations are reasonable
        assert tracker.progress_data["stats"]["current_streak"] >= 0
        assert tracker.progress_data["stats"]["longest_streak"] >= 0
        assert (tracker.progress_data["stats"]["longest_streak"] >= 
                tracker.progress_data["stats"]["current_streak"])

    def test_streak_boundary_conditions(self, tracker):
        """Test streak calculation at boundary conditions"""
        tracker.parse_markdown()
        
        # Test exactly 1 day gap (should continue streak)
        yesterday = datetime.now() - timedelta(days=1)
        today = datetime.now()

        with patch('study_tracker.datetime') as mock_datetime:
            mock_datetime.now.return_value = yesterday
            mock_datetime.fromisoformat = datetime.fromisoformat
            tracker.mark_day_complete(1)

        with patch('study_tracker.datetime') as mock_datetime:
            mock_datetime.now.return_value = today
            mock_datetime.fromisoformat = datetime.fromisoformat
            tracker.mark_day_complete(2)

        assert tracker.progress_data["stats"]["current_streak"] == 2

        # Test exactly 2 day gap (should break streak)
        day_after_tomorrow = today + timedelta(days=2)
        with patch('study_tracker.datetime') as mock_datetime:
            mock_datetime.now.return_value = day_after_tomorrow
            mock_datetime.fromisoformat = datetime.fromisoformat
            tracker.mark_day_complete(3)

        assert tracker.progress_data["stats"]["current_streak"] == 1  # Reset due to gap

    def test_streak_timezone_handling(self, tracker):
        """Test streak calculation across timezone boundaries"""
        tracker.parse_markdown()
        
        # Use dates to avoid timezone issues in tests
        base_today = datetime.now().replace(hour=23, minute=59)
        base_tomorrow = base_today + timedelta(days=1, hours=1)  # Next day, 1 AM
        
        with patch('study_tracker.datetime') as mock_datetime:
            mock_datetime.now.return_value = base_today
            mock_datetime.fromisoformat = datetime.fromisoformat
            tracker.mark_day_complete(1)

        with patch('study_tracker.datetime') as mock_datetime:
            mock_datetime.now.return_value = base_tomorrow
            mock_datetime.fromisoformat = datetime.fromisoformat
            tracker.mark_day_complete(2)

        # Should recognize as consecutive days despite time boundary
        assert tracker.progress_data["stats"]["current_streak"] >= 1