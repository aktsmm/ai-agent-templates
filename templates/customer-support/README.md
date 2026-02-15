# 🤖 Customer Support Agent Template

> AI-powered customer support automation using [CrewAI](https://github.com/crewAIInc/crewAI). Classifies inquiries, answers FAQs, creates tickets, and escalates urgent issues — all with multi-agent orchestration.

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![CrewAI](https://img.shields.io/badge/CrewAI-1.9%2B-green.svg)](https://github.com/crewAIInc/crewAI)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-47%20passed-brightgreen.svg)](#testing)

## Features

- **Multi-Agent Architecture** — Classifier routes to specialized agents (no wasted tokens)
- **YAML-Driven Configuration** — Customize agents & tasks without touching code
- **Multiple LLM Providers** — OpenAI, Azure OpenAI, Anthropic, Ollama (local)
- **3 CLI Modes** — Interactive, single query, batch processing
- **Knowledge Base RAG** — Drop-in Markdown FAQ files for instant answers
- **47 Unit Tests** — Comprehensive test suite with mocked LLM calls

## How It Works

```
Customer Inquiry
       |
       v
+------------------+
| Classifier Agent |  <-- Routes to the right specialist
+--------+---------+
         |
   +-----+-----+
   |     |     |
   v     v     v
 FAQ   Ticket  Escalation
Agent  Agent    Agent
```

| Agent                  | Role                                         | Model                      |
| ---------------------- | -------------------------------------------- | -------------------------- |
| **Classifier**         | Triages inquiries into faq/ticket/escalation | gpt-4o-mini (cheap & fast) |
| **FAQ Specialist**     | Answers common questions from knowledge base | gpt-4o                     |
| **Ticket Handler**     | Creates structured support tickets           | gpt-4o                     |
| **Escalation Manager** | Prepares urgent issue reports for humans     | gpt-4o                     |

## Quick Start

### 1. Install

```bash
# Using pip
pip install -e .

# Using uv (recommended, faster)
uv pip install -e .
```

### 2. Configure

```bash
cp .env.example .env
# Edit .env with your API key
```

### 3. Run

```bash
# Interactive mode
python -m customer_support

# Single query
python -m customer_support --query "How do I reset my password?"

# Classify only (no response generation — saves tokens)
python -m customer_support --query "My payment was charged twice" --classify-only

# Batch mode (one query per line, # comments ignored)
python -m customer_support --file queries.txt
```

## Customization

### Change the LLM Provider

Edit `.env`:

```bash
# OpenAI (default)
MODEL=gpt-4o
OPENAI_API_KEY=sk-your-key-here

# Azure OpenAI
MODEL=azure/gpt-4o
AZURE_API_KEY=your-key
AZURE_API_BASE=https://your-resource.openai.azure.com/
AZURE_API_VERSION=2024-12-01-preview

# Anthropic
MODEL=anthropic/claude-sonnet-4-5-20250929
ANTHROPIC_API_KEY=sk-ant-your-key-here

# Local (Ollama)
MODEL=ollama/llama3
OLLAMA_BASE_URL=http://localhost:11434
```

> **Azure OpenAI Note**: CrewAI uses `AZURE_API_KEY` (not `AZURE_OPENAI_API_KEY`).
> If using `crewai[azure-ai-inference]`, install it explicitly:
>
> ```bash
> pip install "crewai[azure-ai-inference]"
> ```

### Add Your Knowledge Base

Replace or add files in `src/customer_support/knowledge/`:

```
knowledge/
  faq_sample.md      <-- Replace with your FAQ
  product_docs.md    <-- Add product documentation
  policies.md        <-- Add policies, terms, etc.
```

### Customize Agent Behavior

Edit YAML configuration files — no code changes needed:

- `src/customer_support/config/agents.yaml` — Agent roles, goals, backstories
- `src/customer_support/config/tasks.yaml` — Task descriptions and expected outputs

### Add Custom Tools

Create new tools in `src/customer_support/tools/`:

```python
from crewai.tools import tool

@tool("search_tickets")
def search_tickets(query: str) -> str:
    """Search existing support tickets."""
    # Connect to your ticket system (Zendesk, Jira, etc.)
    ...
```

## Project Structure

```
customer-support-agent-template/
+-- .env.example            # Environment config template
+-- pyproject.toml           # Dependencies & project metadata
+-- LICENSE                  # Apache 2.0 License
+-- README.md
+-- src/
|   +-- customer_support/
|       +-- main.py          # Entry point (CLI)
|       +-- crew.py          # Agent & task definitions
|       +-- config/
|       |   +-- agents.yaml  # Agent configuration
|       |   +-- tasks.yaml   # Task configuration
|       +-- tools/
|       |   +-- custom_tool.py  # Knowledge base search
|       +-- knowledge/
|           +-- faq_sample.md   # Sample FAQ data
+-- tests/
    +-- test_crew.py         # Unit tests
```

## Example Output

**Input:** `"My payment was charged twice and I need an immediate refund"`

**Classification:** `escalation`

**Response:**

```
**Severity**: P1-Critical
**Business Impact**: Customer charged incorrectly, potential chargeback risk
**Customer Sentiment**: Frustrated
**Issue Summary**: Double charge on customer payment requiring immediate refund
**Root Cause Hypothesis**: Payment gateway timeout causing duplicate transaction
**Immediate Actions Required**:
  1. Verify double charge in payment system
  2. Initiate immediate refund for duplicate charge
  3. Send confirmation email to customer
  4. Flag transaction for payment team review
**Recommended Resolution Timeline**: 2-4 hours
```

## Testing

```bash
pip install -e ".[dev]"
pytest -v
```

47 tests covering:

- Knowledge base search (7 tests)
- Classification normalization with parametrize (12 tests)
- SupportResult Pydantic model (6 tests)
- YAML configuration validation (4 tests)
- Agent/Task factory with mocks (5 tests)
- classify_inquiry / handle_inquiry integration (6 tests)
- CLI argument parsing (4 tests)
- Environment & security checks (3 tests)

## Troubleshooting

| Problem                                          | Solution                                                           |
| ------------------------------------------------ | ------------------------------------------------------------------ |
| `ModuleNotFoundError: crewai`                    | Run `pip install -e .` in the project root                         |
| `AZURE_OPENAI_API_KEY` not working               | CrewAI uses `AZURE_API_KEY` — rename the env var                   |
| `azure-ai-inference` import error                | Run `pip install "crewai[azure-ai-inference]"`                     |
| `setuptools.backends._legacy` error              | Ensure `build-backend = "setuptools.build_meta"` in pyproject.toml |
| Knowledge base returns "No relevant information" | Add Markdown files to `src/customer_support/knowledge/`            |

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feat/my-feature`
3. Run tests: `pytest -v`
4. Commit (Conventional Commits): `git commit -m "feat: add new tool"`
5. Push and open a Pull Request

## License

Apache 2.0 - See [LICENSE](LICENSE) for details.

## More Templates

Check out our other AI agent templates:

- 💼 Subsidy Consultant Agent (grant matching for Japanese SMEs)
- 🛒 E-commerce Assistant (coming soon)
- ⚖️ Legal Document Analyzer (coming soon)

---

Built with [CrewAI](https://github.com/crewAIInc/crewAI) | [Get more templates](https://github.com/your-username/ai-agent-templates)
