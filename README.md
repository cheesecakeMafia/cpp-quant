# C++ Quantitative Finance Study Tracker

A sophisticated Python CLI tool designed to track and manage progress through a comprehensive 6-month C++ learning journey focused on quantitative finance applications. This tool helps you stay organized, motivated, and on track while mastering C++ for high-performance financial computing.

## 🎯 Project Overview

This study tracker manages a **168-day structured learning path** divided into 4 phases:

1. **Phase 1: C++ Fundamentals** (Weeks 1-8) - Basic syntax, OOP, STL
2. **Phase 2: Advanced C++ & Data Structures** (Weeks 9-16) - Modern C++, algorithms
3. **Phase 3: Advanced DSA & Quant Libraries** (Weeks 17-20) - QuantLib, optimization
4. **Phase 4: Quantitative Finance Specialization** (Weeks 17-24) - Trading systems, low-latency

### Key Features

- ✅ **Progress Tracking**: Mark daily study sessions complete with automatic checkbox updates
- 📊 **Rich Statistics**: Streak tracking, completion percentages, project counts
- 📅 **Smart Planning**: View next tasks, week summaries, and milestone progress
- 🔄 **Undo Functionality**: Reverse accidental completions
- 💾 **Persistent Storage**: Progress saved in hidden JSON file
- 🎨 **Beautiful CLI**: Rich console output with tables, panels, and progress bars
- 📈 **Performance Metrics**: Track study frequency and estimate completion dates

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) package manager (recommended)

### Installation

```bash
# Clone the repository
git clone https://github.com/cheesecakeMafia/cpp-quant
cd cpp-quant

# Install dependencies with uv (recommended)
uv sync

# Activate virtual environment
source .venv/bin/activate

# Alternative: Using pip
pip install -r requirements.txt
```

### First Run

```bash
# Check your current progress (default command)
python study_tracker.py

# Or use the installed script
uv run study

# Mark today's study session as complete
python study_tracker.py --done
```

## 📖 Usage Guide

### Core Commands

#### Progress Tracking
```bash
# View current status (default)
python study_tracker.py --status
python study_tracker.py  # same as above

# Mark current day complete
python study_tracker.py --done

# Undo last completion (if you made a mistake)
python study_tracker.py --undo
```

#### Planning & Navigation
```bash
# See what's next
python study_tracker.py --next

# View current week summary
python study_tracker.py --week-summary

# Jump to a specific day (marks all previous days complete)
python study_tracker.py --jump-to 42
```

#### Analytics & Insights
```bash
# Detailed statistics and projections
python study_tracker.py --stats

# Create backup of study plan
python study_tracker.py --backup
```

### Example Workflow

```bash
# Monday morning - check what's planned
python study_tracker.py --next

# After completing study session
python study_tracker.py --done

# Friday - review week progress
python study_tracker.py --week-summary

# Monthly - check overall statistics
python study_tracker.py --stats
```

## 📊 Sample Output

### Status View
```
┌─────────────────── 📊 Study Progress ───────────────────┐
│ Current: Day 45/168 (26.8%)                           │
│ Phase: PHASE 2: ADVANCED C++ & DATA STRUCTURES        │
│ This Week: 3/7 days completed (Week 7)                │
│ Total Study Sessions: 45                              │
│ Current Streak: 3 days                                │
│ Longest Streak: 12 days                               │
│ Next Milestone: Day 84 - Junior C++ Level (39 days)   │
│ Projects Completed: 4/8 mini, 2/8 major               │
└────────────────────────────────────────────────────────┘
```

### Next Day View
```
┌─────────────────── 📅 Next Study Session ──────────────────┐
│ Day 46 - Week 7                                           │
│ PHASE 2: ADVANCED C++ & DATA STRUCTURES                   │
│                                                            │
│ Tasks:                                                     │
│   • Watch: STL containers                                  │
│   • Code: Map for order book                              │
│   • Practice: Set for unique prices                       │
│   • Container selection guide                             │
│                                                            │
│ 📝 Project Day - Allow extra time!                        │
└────────────────────────────────────────────────────────────┘
```

## 🗂️ Project Structure

```
cpp-quant/
├── study_tracker.py           # Main CLI application
├── cpp-quant-study-plan.md   # 168-day learning curriculum
├── .study_progress.json      # Hidden progress file (auto-generated)
├── tests/                    # Comprehensive test suite
│   ├── test_study_tracker.py # Unit and integration tests
│   ├── conftest.py          # Test fixtures
│   └── README.md            # Testing documentation
├── htmlcov/                 # Coverage reports (generated)
├── pyproject.toml          # uv configuration and dependencies
├── run_test.sh            # Test runner script
└── README.md             # This file
```

## 🎓 Study Plan Overview

The curriculum is designed for **1 hour weekdays + 2 hours weekends** (9 hours/week total):

### Phase 1: C++ Fundamentals (Weeks 1-8)
- Environment setup and basic syntax
- Control structures and functions
- Arrays, strings, and pointers
- Object-oriented programming
- Templates and STL introduction
- Exception handling and file I/O

### Phase 2: Advanced C++ & Data Structures (Weeks 9-16)
- Smart pointers and modern C++
- Advanced algorithms and matrices
- Linked lists, stacks, and queues
- Trees and heaps
- Hash tables and graphs

### Phase 3: Advanced DSA & Quant Libraries (Weeks 17-20)
- Sorting and searching algorithms
- Dynamic programming
- String algorithms
- Introduction to QuantLib and Boost

### Phase 4: Quantitative Finance Specialization (Weeks 21-24)
- Network programming for market data
- Low-latency optimization techniques
- Complete algorithmic trading system
- Final projects and assessment

### Key Projects
- **Mini Projects** (8): Financial calculator, Monte Carlo pricer, order book, etc.
- **Major Projects** (8): Trading engine, limit order book, correlation network, etc.

## 🧪 Testing

The project includes a comprehensive test suite with **32 test cases** covering:

- Core functionality (parsing, progress tracking)
- CLI interface testing
- Edge cases and error conditions
- Unicode support and concurrent modifications

### Running Tests

```bash
# Run all tests with coverage
source run_test.sh

# Quick test run
source run_test.sh quick

# Verbose output
source run_test.sh verbose

# Or use uv directly
uv run pytest --cov=study_tracker --cov-report=html
```

### Test Coverage
Current test coverage: **65%** with detailed HTML reports generated in `htmlcov/`.

## ⚙️ Configuration

### Dependencies
- **Rich**: Beautiful terminal output and formatting
- **pytest**: Testing framework with coverage reporting
- **python-dotenv**: Environment variable management

### Customization

You can modify the study plan by editing `cpp-quant-study-plan.md`. The tracker automatically:
- Detects day headers (`#### Day X`)
- Associates checkboxes with the current day
- Tracks week and phase information

### Progress Data
Progress is stored in `.study_progress.json` with:
- Completed days list
- Study session history
- Streak statistics
- Timestamps for all activities

## 🚀 Advanced Usage

### Scripting Integration
```bash
# Check if ready for next milestone
if python study_tracker.py --status | grep -q "Day 84"; then
    echo "Junior C++ level achieved!"
fi

# Daily reminder script
python study_tracker.py --next | head -n 10
```

### Performance Optimization
The tracker is optimized for:
- Fast markdown parsing (handles 1000+ day curriculum)
- Efficient checkbox state management
- Minimal memory footprint
- Quick startup time

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`source run_test.sh`)
5. Commit changes (`git commit -m 'Add amazing feature'`)
6. Push to branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

### Development Setup
```bash
# Install development dependencies
uv sync --dev

# Run tests in watch mode
source run_test.sh watch

# Generate coverage report
uv run pytest --cov=study_tracker --cov-report=html
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Course Materials**: Based on comprehensive C++ and quantitative finance curricula
- **Rich Library**: For beautiful terminal output
- **uv**: For modern Python package management
- **QuantLib Community**: For inspiration on quant finance applications

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/cheesecakeMafia/cpp-quant/issues)
- **Discussions**: Use GitHub Discussions for questions
- **Documentation**: See `tests/README.md` for testing details

---

**Happy studying! 🚀 Master C++ for quantitative finance in 6 months!**