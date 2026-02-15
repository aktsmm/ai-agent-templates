# Contributing to AI Agent Templates

Thank you for your interest in contributing! This guide will help you get started.

## Development Setup

```bash
# Clone & navigate to a template
git clone https://github.com/your-username/ai-agent-templates.git
cd ai-agent-templates/templates/customer-support

# Create venv & install dev dependencies
python -m venv .venv
source .venv/bin/activate      # Linux/macOS
# .\.venv\Scripts\Activate.ps1  # Windows
pip install -e ".[dev]"
```

## Code Style

- **Python**: Formatted with [Ruff](https://github.com/astral-sh/ruff) (line-length 100)
- **Variables/Functions**: English, `snake_case`
- **Comments/Docs**: Japanese or English (Japanese preferred for JP-specific templates)
- **Type Hints**: Required for all function signatures

```bash
# Lint
ruff check src/ tests/
ruff format --check src/ tests/

# Fix
ruff check --fix src/ tests/
ruff format src/ tests/
```

## Testing

- All tests must pass without API keys (mock all LLM calls)
- Use `pytest` with `unittest.mock.patch` for CrewAI components
- Add tests for new features before submitting PR

```bash
pytest -v
```

## Commit Convention

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add new search tool for subsidy database
fix: handle empty query in knowledge base search
test: add edge case tests for classification
docs: update README with Azure setup instructions
refactor: extract YAML loading into helper function
```

## Pull Request Process

1. Fork the repository
2. Create a feature branch: `git checkout -b feat/my-feature`
3. Make changes with tests
4. Run `pytest -v` and `ruff check` — both must pass
5. Commit with conventional commits
6. Push and open a PR with a clear description

## Adding a New Template

1. Copy `templates/customer-support/` as a starting point
2. Update `pyproject.toml` with new package name and description
3. Create `config/agents.yaml` and `config/tasks.yaml`
4. Implement `crew.py` (agent factory + public API functions)
5. Implement `main.py` (CLI entry point)
6. Add knowledge base data in `knowledge/`
7. Write comprehensive tests (target: 20+ tests)
8. Create `README.md` with Quick Start, Customization, and Troubleshooting
9. Add `setup.sh` and `setup.ps1`
10. Update the root `README.md` template table

## Questions?

Open an issue or start a discussion.
