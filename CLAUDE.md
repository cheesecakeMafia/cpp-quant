# Standard Workflow for projects to follow
1. First think through the problem, read the codebase for relevant files, and write a plan to project_plan.md
2. The plan should have a list of todo items that you can check off as you complete them.
3. Before you begin working, check in with me and I will verify the plan.
4. Then, begin working on the todo items, marking them as complete as you go.
5. When writing code, also write comprehensive tests in the tests/ folder:
   - Create unit tests in tests/unit/ directory
   - Create integration tests in tests/integration/ directory
   - Use pytest as the testing framework
6. Please every step of the way just give me a high level explanation of what changes you made
7. Make every task and code change you do as simple as possible. We want to avoid making any massive or complex changes. Every change should impact as little code as possible. Everything is about simplicity.
8. Finally, add a review section to the projectplan.md file with a summary of the changes you made and any other relevant information.

# Personal Development Preferences
- Python 3.12+ preferred
- Use uv for package management and virtual environments
- Use type hints for all functions and variables
- Prefer dataclasses and Pydantic models for data structures
- Use pathlib for file operations
- Follow PEP 8 and modern Python practices

# Code Style
- Use f-strings for string formatting
- Prefer if/elif statements over match/case
- Use context managers (with statements) for resource management
- Use list/dict comprehensions when readable
- Use Union types with | operator (Python 3.10+)

# Package Management with uv
- Create project: `uv init`
- Add dependencies: `uv add package-name`
- Add dev dependencies: `uv add --dev package-name`
- Run Python files: `uv run file_name.py`
- Run scripts: `uv run script-name`
- Install dependencies: `uv sync`
- Activate environment: `source .venv/bin/activate`

# Project Structure Preferences
- Use pyproject.toml for configuration (uv creates this by default)
- Organize code in packages with __init__.py
- Keep tests in separate tests/ directory
- Use .env files for environment variables with python-dotenv (pre-installed)

# Modern Python Features
- Use Union types with | operator (Python 3.10+)
- Leverage new typing features from Python 3.12+
- Use @property and @cached_property for computed attributes
- Prefer async/await for I/O operations when applicable

# Default Packages (pre-installed via bash script)
- python-dotenv for environment variables
- Other packages as configured in your bash script

# Development Workflow
- Projects managed with uv virtual environments
- Dependencies declared in pyproject.toml
- Use uv run for executing commands in project context

