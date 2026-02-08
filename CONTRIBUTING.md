# Contributing to OmniMRZ

Thank you for your interest in contributing to OmniMRZ! We welcome contributions from the community.

## Development Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/AzwadFawadHasan/OmniMRZ.git
   cd OmniMRZ
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -e ".[dev]"
   ```

## Development Workflow

1. **Create a feature branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes and write tests**

3. **Run tests:**
   ```bash
   pytest
   ```

4. **Run code quality checks:**
   ```bash
   black .  # Format code
   isort .  # Sort imports
   flake8 . # Check style
   ```

5. **Commit your changes:**
   ```bash
   git commit -m "Add your descriptive commit message"
   ```

6. **Push and create a pull request:**
   ```bash
   git push origin feature/your-feature-name
   ```

## Code Style

- Follow PEP 8 style guidelines
- Use type hints where appropriate
- Write docstrings for all public functions and classes
- Keep functions small and focused on a single responsibility

## Testing

- Write unit tests for all new functionality
- Aim for high test coverage
- Test both success and failure cases
- Use descriptive test names

## Documentation

- Update README.md for any user-facing changes
- Update docstrings for code changes
- Add examples for new features

## Reporting Issues

When reporting bugs, please include:
- Python version
- Operating system
- Steps to reproduce
- Expected vs actual behavior
- Any relevant error messages

## License

By contributing to this project, you agree that your contributions will be licensed under the same license as the project (Apache 2.0).