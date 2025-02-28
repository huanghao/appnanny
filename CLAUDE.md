# AppNanny Codebase Guidelines

## Build & Run Commands
- Run Flask API: `python apps.py`
- Run Streamlit UI: `streamlit run admin.py`
- Install dependencies: `pip install -r requirements.txt`
- Lint code: `flake8 *.py`
- Type check: `mypy *.py`

## Testing
- Run tests: `pytest tests/`
- Run a single test: `pytest tests/test_file.py::test_function`

## Code Style Guidelines
- **Imports**: Group standard library, third-party, and local imports with a blank line between groups
- **Formatting**: Follow PEP 8 style guide with 4 spaces for indentation
- **Error Handling**: Use try/except blocks with specific exceptions, log errors appropriately
- **Logging**: Use the configured logger with appropriate log levels (info, warning, error)
- **Environment Variables**: Access through env_vars dictionary, convert values to appropriate types
- **Types**: Use type hints for function parameters and return values
- **Documentation**: Include docstrings for functions and classes following the triple-quote style

## Architecture
- Flask API for backend operations
- Streamlit for frontend UI
- File-based storage for app metadata
- Threading for concurrent API and scheduler execution