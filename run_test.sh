#!/bin/bash
# Test runner script for study_tracker.py

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "🧪 Running Study Tracker Tests..."
echo "================================"

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo -e "${RED}pytest is not installed. Please run: pip install -r requirements.txt${NC}"
    exit 1
fi

# Run tests with coverage by default
if [ "$1" == "quick" ]; then
    # Quick run without coverage
    echo "Running tests (quick mode)..."
    pytest
elif [ "$1" == "watch" ]; then
    # Watch mode (requires pytest-watch)
    echo "Running tests in watch mode..."
    pip install pytest-watch 2>/dev/null
    ptw
elif [ "$1" == "verbose" ]; then
    # Very verbose output
    echo "Running tests (verbose mode)..."
    pytest -vv
else
    # Default: run with coverage
    echo "Running tests with coverage..."
    pytest --cov=study_tracker --cov-report=term-missing --cov-report=html
    
    echo ""
    echo -e "${GREEN}✅ Tests complete!${NC}"
    echo "Coverage report generated in htmlcov/index.html"
fi

# Show test summary
echo ""
echo "Test Summary:"
echo "============="
pytest --tb=no -q | tail -n 5