# 📊 Sales Lead Qualifier Agent Template

> AI-powered B2B sales lead qualification using CrewAI. Scores leads with BANT,
> researches companies, composes outreach emails, and handles objections — all with
> multi-agent orchestration.

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![CrewAI](https://img.shields.io/badge/CrewAI-1.9%2B-green.svg)](https://github.com/crewAIInc/crewAI)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-passing-brightgreen.svg)](#testing)

## Features

- **Multi-Agent Architecture** — Classifier routes to 4 specialized sales agents
- **BANT Lead Scoring** — Budget, Authority, Need, Timeline framework (0-100 score)
- **YAML-Driven Configuration** — Customize agents & tasks without touching code
- **Multiple LLM Providers** — OpenAI, Azure OpenAI, Anthropic, Ollama (local)
- **3 CLI Modes** — Interactive, single query, batch processing
- **Lead Database** — Drop-in Markdown knowledge base for prospect data
- **Comprehensive Tests** — Full test suite with mocked LLM calls

## How It Works

```
Sales Request → Classifier Agent → [Lead Scorer / Company Researcher / Email Composer / Objection Handler] specialist
```

### Agent Roles

| Agent                  | Role                                           | Tools                                    |
| ---------------------- | ---------------------------------------------- | ---------------------------------------- |
| **Classifier**         | Routes requests to the right specialist        | —                                        |
| **Lead Scorer**        | Scores leads using BANT framework (0-100)      | `search_lead_database`, `lookup_company` |
| **Company Researcher** | Provides company intelligence & talking points | `search_lead_database`, `lookup_company` |
| **Email Composer**     | Writes personalized sales emails               | `search_lead_database`, `lookup_company` |
| **Objection Handler**  | Prepares data-backed objection responses       | `search_lead_database`                   |

### Categories

| Category             | Trigger Examples                                                 |
| -------------------- | ---------------------------------------------------------------- |
| `lead_scoring`       | "Score TechFlow Solutions", "Qualify this prospect"              |
| `company_research`   | "Research MediCore Health", "Find decision-makers at GlobalMart" |
| `email_outreach`     | "Write a cold email to Sarah Chen", "Draft a follow-up"          |
| `objection_handling` | "They said pricing is too high", "Handle 'we use a competitor'"  |

## Quick Start

```bash
# 1. Setup (auto: venv + deps + .env)
bash setup.sh        # Linux / macOS
.\setup.ps1          # Windows

# 2. Configure
# Edit .env and add your API key

# 3. Run
python -m sales_lead_qualifier --query "Score TechFlow Solutions as a lead"
```

## Usage

```bash
# Interactive mode (default)
python -m sales_lead_qualifier

# Single query
python -m sales_lead_qualifier --query "Research MediCore Health for our next call"

# Classify only (no specialist response)
python -m sales_lead_qualifier --query "Write a cold email" --classify-only

# Batch mode
python -m sales_lead_qualifier --file queries.txt
```

## Project Structure

```
sales-lead-qualifier/
├── src/sales_lead_qualifier/
│   ├── __init__.py
│   ├── __main__.py          # python -m entry point
│   ├── main.py              # CLI with 3 modes
│   ├── crew.py              # Agent/Task/Crew definitions
│   ├── config/
│   │   ├── agents.yaml      # Agent roles & backstories
│   │   └── tasks.yaml       # Task descriptions & expected outputs
│   ├── knowledge/
│   │   └── lead_database.md # Sample lead & company data (replaceable)
│   └── tools/
│       ├── __init__.py
│       └── custom_tool.py   # search_lead_database, lookup_company
├── tests/
│   └── test_crew.py         # Full test suite (mocked, no API keys)
├── .env.example              # Template environment config
├── pyproject.toml            # Project metadata & deps
├── setup.sh / setup.ps1      # One-click setup scripts
└── README.md
```

## Configuration

### Environment Variables

| Variable           | Default       | Description                      |
| ------------------ | ------------- | -------------------------------- |
| `MODEL`            | `gpt-4o`      | Main LLM for specialist agents   |
| `CLASSIFIER_MODEL` | `gpt-4o-mini` | Cheaper model for classification |
| `OPENAI_API_KEY`   | —             | Your OpenAI API key              |
| `VERBOSE`          | `true`        | Show agent reasoning in console  |
| `LOG_LEVEL`        | `INFO`        | Logging verbosity                |

### Customization

1. **Leads**: Edit `src/sales_lead_qualifier/knowledge/lead_database.md`
2. **Agent behavior**: Edit `src/sales_lead_qualifier/config/agents.yaml`
3. **Task prompts**: Edit `src/sales_lead_qualifier/config/tasks.yaml`
4. **Tools**: Add real CRM backends in `src/sales_lead_qualifier/tools/custom_tool.py`

## Testing

```bash
# Run all tests
pytest -v

# Run with coverage
pytest --cov=sales_lead_qualifier -v
```

All tests are fully mocked — **no API keys or LLM calls required**.

## Extending

### Connect to a Real CRM

Replace the sample data in `tools/custom_tool.py` with:

- **Salesforce API** / **HubSpot API** for lead and company data
- **LinkedIn Sales Navigator** for prospect research
- **Clearbit** / **ZoomInfo** for company enrichment
- **Your own CRM REST API** for customer data

### Add Email Integration

Extend the email composer to:

- **SendGrid** / **Mailgun** for automated email sending
- **Gmail API** for draft creation
- **Outreach.io** / **Salesloft** for sequence automation

### Enhance Lead Scoring

Upgrade the BANT scoring with:

- **Predictive scoring** using historical win/loss data
- **Intent signals** from website analytics (6sense, Bombora)
- **Engagement scoring** from email opens, clicks, and page visits

## License

[Apache 2.0](LICENSE)
