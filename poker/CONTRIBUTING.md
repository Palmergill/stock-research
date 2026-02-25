# Contributing to the Poker App

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+ (for frontend tooling)
- Git

### Setup

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/YOUR_USERNAME/stock-research.git
   cd stock-research/poker
   ```

3. Set up the backend:
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements-dev.txt
   ```

4. Run tests to ensure everything works:
   ```bash
   pytest
   ```

## Development Workflow

### Running the Backend Locally

```bash
cd backend
python main.py
```

The API will be available at `http://localhost:8000` with docs at `/docs`.

### Frontend Development

The frontend is vanilla HTML/CSS/JS. Simply open `index.html` in a browser or use a local server:

```bash
cd poker
python -m http.server 8080
```

### Running Tests

```bash
cd backend
pytest                    # Run all tests
pytest -v               # Verbose output
pytest -k test_name     # Run specific test
pytest --cov=app        # With coverage report
```

## Code Style

### Python

- Follow PEP 8
- Use type hints where possible
- Maximum line length: 100 characters
- Use docstrings for public functions

Example:
```python
def calculate_pot(players: list[Player]) -> int:
    """Calculate the total pot from all player bets.
    
    Args:
        players: List of active players in the hand
        
    Returns:
        Total pot size in chips
    """
    return sum(p.current_bet for p in players)
```

### JavaScript

- Use ES6+ features
- Prefer `const` and `let` over `var`
- Use camelCase for variables/functions
- Use PascalCase for classes
- Add JSDoc comments for complex functions

## Making Changes

### Branch Naming

- `feature/description` - New features
- `bugfix/description` - Bug fixes
- `docs/description` - Documentation updates
- `refactor/description` - Code refactoring

### Commit Messages

Use clear, descriptive commit messages:

```
[v1.0.5] Add hand history export feature

- Add JSON export button to UI
- Implement /api/poker/games/{id}/export endpoint
- Add tests for export functionality
```

Include the version number in brackets for releases.

## Submitting Changes

1. Create a new branch for your changes
2. Make your changes with clear commits
3. Add/update tests as needed
4. Ensure all tests pass: `pytest`
5. Update relevant documentation
6. Push to your fork
7. Create a Pull Request

### Pull Request Guidelines

- Provide a clear description of changes
- Reference any related issues
- Ensure CI checks pass
- Request review from maintainers

## Areas Needing Help

Check `TASKS.md` for incomplete tasks. Priority areas:

- **AI Improvements**: Better decision-making algorithms
- **Testing**: Frontend unit tests with Jest/Vitest
- **Documentation**: User guides, API docs
- **Performance**: WebSocket migration from polling

## Reporting Issues

When reporting bugs, please include:

- Browser/device info
- Steps to reproduce
- Expected vs actual behavior
- Screenshots if applicable
- Error messages from console

## Code of Conduct

- Be respectful and inclusive
- Welcome newcomers
- Focus on constructive feedback
- Assume good intentions

## Questions?

Open an issue or reach out to the maintainers.

---

Thank you for contributing! 🎉
