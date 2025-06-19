# Study Tracker Tests

## Setup

1. Install test dependencies:
```bash
pip install -r requirements.txt
```

2. Directory structure:
```
cpp-quant-journey/
├── cpp-quant-study-plan.md
├── study_tracker.py
├── requirements.txt
├── pytest.ini
└── tests/
    ├── README.md
    └── test_study_tracker.py
```

## Running Tests

### Run all tests:
```bash
pytest
```

### Run with coverage report:
```bash
pytest --cov=study_tracker --cov-report=html
# Open htmlcov/index.html to view coverage report
```

### Run specific test class:
```bash
pytest tests/test_study_tracker.py::TestStudyTracker -v
```

### Run specific test:
```bash
pytest tests/test_study_tracker.py::TestStudyTracker::test_mark_day_complete -v
```

### Run tests with more verbose output:
```bash
pytest -vv
```

### Run tests and stop on first failure:
```bash
pytest -x
```

## Test Categories

The test suite includes:

1. **Unit Tests** (`TestStudyTracker`)
   - Core functionality like marking days complete
   - Progress tracking and calculations
   - File operations

2. **CLI Tests** (`TestCLIFunctionality`)
   - Command-line argument handling
   - User interface behavior

3. **Edge Cases** (`TestEdgeCases`)
   - Unicode handling
   - Concurrent modifications
   - Error conditions

## Writing New Tests

When adding new features to `study_tracker.py`, please add corresponding tests:

1. Create test methods starting with `test_`
2. Use descriptive names (e.g., `test_mark_day_complete_with_invalid_day`)
3. Follow the Arrange-Act-Assert pattern
4. Mock external dependencies (file I/O, console output)

Example:
```python
def test_new_feature(self, tracker):
    """Test description of what this tests"""
    # Arrange
    tracker.parse_markdown()
    
    # Act
    result = tracker.new_feature()
    
    # Assert
    assert result == expected_value
```

## Continuous Integration

You can add this to your GitHub Actions workflow:

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - uses: actions/setup-python@v2
      with:
        python-version: '3.x'
    - name: Install dependencies
      run: pip install -r requirements.txt
    - name: Run tests
      run: pytest --cov=study_tracker
```