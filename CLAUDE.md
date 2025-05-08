# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands
- Run application: `python main.py [--url LOGIN_URL] [--headless]`
- Install Chrome driver: `python install_chrome_driver.py`
- Testing: Test examples are in `test.ipynb`

## Project Structure
- Selenium-based automation for online lecture attendance
- Textual framework for TUI (Terminal User Interface)
- Python 3.12+ required

## Code Style Guidelines
- Imports: Group by standard library, third-party, local modules
- Types: Use type hints where appropriate
- Error handling: Use try/except blocks with specific exceptions
- Naming: snake_case for variables/functions, PascalCase for classes
- Documentation: Add docstrings to functions and classes
- Formatting: 4-space indentation, 88 character line limit

## Keyboard Commands
- `q`: Exit
- `d`: Toggle dark mode
- `r`: Refresh
- `enter`: Start auto-attendance
- `re-enter`: Stop attendance