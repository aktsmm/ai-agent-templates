# 🖥️ IT Helpdesk Agent

> AI-powered internal IT support agent that handles password resets, software troubleshooting, network diagnostics, and hardware issues.

## Features

| Category          | What it does                                                      |
| ----------------- | ----------------------------------------------------------------- |
| 🔑 Password Reset | Reset passwords, unlock accounts, configure MFA, manage access    |
| 💿 Software Issue | Troubleshoot installs, crashes, updates, licensing, configuration |
| 🌐 Network Issue  | Diagnose VPN, Wi-Fi, DNS, firewall, and connectivity problems     |
| 🖨️ Hardware Issue | Handle laptop, monitor, printer, and peripheral issues            |

## Agents

| Agent                   | Role                               | Tools                         |
| ----------------------- | ---------------------------------- | ----------------------------- |
| Classifier              | Routes requests to specialists     | —                             |
| Password Reset          | IAM & credential management        | Knowledge Base, Ticket Lookup |
| Software Troubleshooter | Software diagnosis & resolution    | Knowledge Base, Ticket Lookup |
| Network Support         | Network connectivity diagnosis     | Knowledge Base, System Status |
| Hardware Support        | Hardware diagnostics & replacement | Knowledge Base, Ticket Lookup |

## Quick Start

```bash
# 1. Setup (auto: venv + deps + .env)
bash setup.sh        # Linux / macOS
.\setup.ps1          # Windows

# 2. Configure
# Edit .env and add your API key

# 3. Run
python -m it_helpdesk --query "I forgot my password"
```

## Usage

```bash
# Interactive mode
python -m it_helpdesk

# Single query
python -m it_helpdesk --query "VPN keeps disconnecting"

# Classify only (no full response)
python -m it_helpdesk --query "printer not working" --classify-only

# Batch mode
python -m it_helpdesk --file requests.txt
```

## Configuration

### LLM Settings (.env)

```bash
# OpenAI (default)
OPENAI_API_KEY=sk-your-key-here
MODEL=gpt-4o
CLASSIFIER_MODEL=gpt-4o-mini

# Azure OpenAI
AZURE_OPENAI_API_KEY=your-key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
MODEL=azure/your-deployment

# Anthropic
ANTHROPIC_API_KEY=sk-ant-your-key
MODEL=anthropic/claude-sonnet-4-20250514

# Ollama (local, free)
MODEL=ollama/llama3.1
```

### Agent Customization

Edit YAML files — no Python changes needed:

- **`config/agents.yaml`** — Agent roles, goals, and backstories
- **`config/tasks.yaml`** — Task descriptions and expected outputs
- **`knowledge/it_knowledge_base.md`** — IT knowledge base articles and procedures

## Project Structure

```
it-helpdesk/
├── pyproject.toml
├── setup.sh / setup.ps1
├── .env.example
├── src/
│   └── it_helpdesk/
│       ├── main.py              # CLI entry point
│       ├── crew.py              # Agent & task definitions
│       ├── config/
│       │   ├── agents.yaml      # Agent configuration
│       │   └── tasks.yaml       # Task configuration
│       ├── tools/
│       │   └── custom_tool.py   # KB search, ticket lookup, system status
│       └── knowledge/
│           └── it_knowledge_base.md  # IT procedures & troubleshooting guides
└── tests/
    └── test_crew.py             # 92 tests (all mocked)
```

## Testing

```bash
pip install -e ".[dev]"
pytest -v  # 92 tests, all mocked — no API keys needed
```

## Extending

### Add a new category

1. Add agent definition to `config/agents.yaml`
2. Add task definition to `config/tasks.yaml`
3. Add the category to `HelpdeskResult.category` Literal type in `crew.py`
4. Add routing entry to `task_map` in `handle_request()`
5. Add normalization rules to `_normalize_category()`
6. Add knowledge base articles to `knowledge/it_knowledge_base.md`

### Add custom tools

1. Create a new `@tool` function in `tools/custom_tool.py`
2. Import and assign to the relevant agent in `_create_agents()`

### Connect to real systems

Replace the sample data in `tools/custom_tool.py` with your actual integrations:

- **Ticket system**: ServiceNow, Jira Service Management, Zendesk
- **Knowledge base**: Confluence, SharePoint, custom KB
- **System status**: Datadog, PagerDuty, StatusPage API
- **Active Directory**: Microsoft Graph API, LDAP

## License

Apache 2.0 — see [LICENSE](LICENSE).
