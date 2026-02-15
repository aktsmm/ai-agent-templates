# 👥 HR Onboarding Assistant

AI-powered HR onboarding assistant that guides new hires through the complete onboarding process using specialized agents.

## What It Does

The assistant classifies onboarding requests and routes them to the appropriate specialist:

| Agent                    | Handles                                                                     |
| ------------------------ | --------------------------------------------------------------------------- |
| **Classifier**           | Routes requests to the right specialist                                     |
| **Document Collector**   | Employment contracts, tax forms, ID verification, bank details, benefits    |
| **IT Setup Coordinator** | Laptop provisioning, email accounts, VPN, badges, access permissions        |
| **Training Scheduler**   | Orientation, compliance training, role-specific courses, 30/60/90-day plans |
| **Buddy Matcher**        | Mentor assignment, team introductions, welcome events, social integration   |

## Quick Start

```bash
# Setup (creates venv, installs deps, copies .env)
bash setup.sh        # Linux / macOS
.\setup.ps1          # Windows

# Edit .env with your API key
# Then run:
python -m hr_onboarding --query "What documents do I need before my start date?"
```

## Usage

```bash
# Interactive mode
python -m hr_onboarding

# Single query
python -m hr_onboarding --query "When is my orientation session?"

# Classify only (no response generation)
python -m hr_onboarding --classify-only --query "I need a laptop"

# Batch mode
python -m hr_onboarding --file requests.txt
```

## Custom Tools

| Tool                      | Description                                                           |
| ------------------------- | --------------------------------------------------------------------- |
| `search_onboarding_guide` | Search the HR knowledge base for procedures, checklists, and policies |
| `lookup_employee`         | Look up a new hire's onboarding record and progress                   |
| `check_onboarding_status` | Check the onboarding pipeline status by department                    |

## Project Structure

```
hr-onboarding/
├── pyproject.toml
├── setup.sh / setup.ps1
├── .env.example
├── src/hr_onboarding/
│   ├── main.py              # CLI entry point
│   ├── crew.py              # Agent & task definitions
│   ├── config/
│   │   ├── agents.yaml      # 5 agent definitions
│   │   └── tasks.yaml       # 5 task definitions
│   ├── tools/
│   │   └── custom_tool.py   # 3 custom tools
│   └── knowledge/
│       └── onboarding_guide.md  # HR knowledge base
└── tests/
    └── test_crew.py          # Comprehensive test suite
```

## Testing

```bash
pip install -e ".[dev]"
pytest -v
```

All tests are mocked — no API keys or LLM calls needed.

## LLM Configuration

Edit `.env` to use your preferred LLM provider. See `.env.example` for options:

- OpenAI (default)
- Azure OpenAI
- Anthropic
- Ollama (local)

## License

Apache 2.0
