# 🤖 AI Agent Templates

> Production-ready, YAML-configurable AI agent templates powered by [CrewAI](https://github.com/crewAIInc/crewAI). Clone, customize, deploy — no ML expertise required.

[![CI](https://github.com/aktsmm/ai-agent-templates/actions/workflows/ci.yml/badge.svg)](https://github.com/aktsmm/ai-agent-templates/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![CrewAI](https://img.shields.io/badge/CrewAI-1.9%2B-green.svg)](https://github.com/crewAIInc/crewAI)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-204%20passed-brightgreen.svg)](#testing)

## Why?

AI agent frameworks are powerful — but going from "hello world" to production takes hours of boilerplate. These templates give you:

- **Multi-agent architecture** out of the box (classifier → specialists)
- **YAML configuration** for agents & tasks (no code changes to customize)
- **Multiple LLM support** (OpenAI, Azure OpenAI, Anthropic, Ollama)
- **CLI with 3 modes** (interactive, single query, batch)
- **Comprehensive test suites** (204 tests, all mocked — no API keys needed)
- **Setup scripts** for instant onboarding

## Templates

| Template                                                         | Description                                                                          | Agents                                               | Tests |
| ---------------------------------------------------------------- | ------------------------------------------------------------------------------------ | ---------------------------------------------------- | ----- |
| [🤖 Customer Support](templates/customer-support/)               | Classify inquiries, answer FAQs (RAG), create tickets, escalate urgent issues        | 4 (Classifier → FAQ / Ticket / Escalation)           | 47    |
| [💼 Subsidy Consultant](templates/subsidy-consultant/)           | Match Japanese SME grants, draft applications, score proposals, summarize guidelines | 4 (Matcher / Writer / Scorer / Summarizer)           | 29    |
| [🛒 E-commerce Assistant](templates/ecommerce-assistant/)        | Search products, track orders, handle returns, recommend items                       | 5 (Classifier → Search / Order / Return / Recommend) | 62    |
| [⚖️ Legal Document Analyzer](templates/legal-document-analyzer/) | Extract clauses, analyze risks, summarize contracts, compare documents               | 5 (Classifier → Clause / Risk / Summary / Compare)   | 66    |
| 📊 Sales Lead Qualifier                                          | _Coming soon_                                                                        | —                                                    | —     |

## Quick Start

```bash
# 1. Clone
git clone https://github.com/your-username/ai-agent-templates.git
cd ai-agent-templates/templates/customer-support

# 2. Setup (auto: venv + deps + .env)
bash setup.sh        # Linux / macOS
.\setup.ps1          # Windows

# 3. Run
python -m customer_support --query "How do I reset my password?"
```

## Architecture

Each template follows the same pattern:

```
template/
├── pyproject.toml          # Dependencies & metadata
├── setup.sh / setup.ps1    # One-command setup
├── .env.example            # LLM config template
├── src/
│   └── <package>/
│       ├── main.py         # CLI entry point
│       ├── crew.py         # Agent & task definitions
│       ├── config/
│       │   ├── agents.yaml # Agent roles, goals, backstories
│       │   └── tasks.yaml  # Task descriptions & expected outputs
│       ├── tools/          # Custom CrewAI tools
│       └── knowledge/      # RAG data (Markdown / YAML)
└── tests/
    └── test_*.py           # Comprehensive test suite
```

**Key design principle**: All agent behavior is defined in YAML. Users customize `agents.yaml` and `tasks.yaml` — no Python changes needed.

## Testing

Each template has its own test suite that runs without API keys (all LLM calls are mocked):

```bash
cd templates/customer-support
pip install -e ".[dev]"
pytest -v  # 47 tests

cd ../subsidy-consultant
pip install -e ".[dev]"
pytest -v  # 29 tests
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

Apache 2.0 — See individual template LICENSE files for details.

---

Built with [CrewAI](https://github.com/crewAIInc/crewAI) | Star ⭐ if useful!
