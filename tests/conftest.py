"""
Shared fixtures for pytest
These fixtures are available to all test files in the tests directory
"""

import pytest
import tempfile
import shutil
import os
from pathlib import Path


@pytest.fixture
def temp_test_dir():
    """Create a temporary directory that's automatically cleaned up"""
    temp_dir = tempfile.mkdtemp(prefix="study_tracker_test_")
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def sample_markdown_content():
    """Provide sample markdown content for testing"""
    return """# C++ Quantitative Finance Learning Path

## 📅 PHASE 1: C++ FUNDAMENTALS (Weeks 1-8)

### Week 1: Setup & C++ Basics
#### Day 1 (1 hour - Weekday)
- [ ] Install g++ compiler and VS Code C++ extensions
- [ ] Configure VS Code for C++ development
- [ ] Create GitHub repo: "cpp-quant-journey"
- [ ] Watch Course 1: Introduction & Course Overview

#### Day 2 (1 hour - Weekday)
- [ ] Watch: C++ Basics - Program Structure
- [ ] Code: First "Hello World" program
- [ ] Mini Project: Hello Quant World
- [ ] Practice: Compile and run from terminal

### Week 2: Control Structures
#### Day 3 (1 hour - Weekday)  
- [ ] Watch: Variables and Data Types
- [ ] Compare C++ types with Python types
- [ ] Project: Type Explorer
- [ ] Note differences: static typing vs dynamic typing
"""


@pytest.fixture
def mock_console(monkeypatch):
    """Mock the rich console to prevent actual output during tests"""
    from unittest.mock import MagicMock

    mock = MagicMock()
    monkeypatch.setattr("study_tracker.console", mock)
    return mock


@pytest.fixture
def isolated_tracker(temp_test_dir, sample_markdown_content):
    """Create a fully isolated tracker instance for testing"""
    import sys
    import os

    # Add parent directory to path if needed
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)

    from study_tracker import StudyTracker

    # Create test files
    markdown_file = os.path.join(temp_test_dir, "test_plan.md")
    progress_file = os.path.join(temp_test_dir, ".test_progress.json")

    # Write sample markdown
    with open(markdown_file, "w", encoding="utf-8") as f:
        f.write(sample_markdown_content)

    # Create and return tracker
    return StudyTracker(markdown_file, progress_file)


@pytest.fixture(autouse=True)
def cleanup_test_files(request):
    """Automatically clean up any test files created during tests"""
    yield

    # Clean up any backup files created during tests
    import glob
    import os

    test_dir = os.path.dirname(request.node.fspath)
    backup_files = glob.glob(os.path.join(test_dir, "*.backup_*"))
    for backup in backup_files:
        try:
            os.remove(backup)
        except:
            pass
