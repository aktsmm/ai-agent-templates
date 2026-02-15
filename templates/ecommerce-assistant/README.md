# 🛒 E-commerce Assistant Agent Template

> AI-powered e-commerce shopping assistant using CrewAI. Searches products,
> tracks orders, handles returns, and recommends items — all with
> multi-agent orchestration.

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![CrewAI](https://img.shields.io/badge/CrewAI-1.9%2B-green.svg)](https://github.com/crewAIInc/crewAI)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-passing-brightgreen.svg)](#testing)

## Features

- **Multi-Agent Architecture** — Classifier routes to 4 specialized agents
- **YAML-Driven Configuration** — Customize agents & tasks without touching code
- **Multiple LLM Providers** — OpenAI, Azure OpenAI, Anthropic, Ollama (local)
- **3 CLI Modes** — Interactive, single query, batch processing
- **Product Catalog Search** — Drop-in Markdown catalog for instant product lookups
- **Order Tracking** — Sample order lookup with extensible backend
- **Comprehensive Tests** — Full test suite with mocked LLM calls

## How It Works

```
Customer Inquiry → Classifier Agent → [Product Search / Order Tracking / Return & Refund / Recommendation] specialist
```

### Agent Roles

| Agent | Role | Tools |
|-------|------|-------|
| **Classifier** | Routes inquiries to the right specialist | — |
| **Product Search** | Finds products, compares options, checks availability | `search_product_catalog` |
| **Order Tracker** | Checks order status, shipping, delivery estimates | `lookup_order` |
| **Return Handler** | Processes returns/refunds, checks eligibility | `search_product_catalog` |
| **Recommender** | Suggests products based on preferences | `search_product_catalog` |

### Categories

| Category | Trigger Examples |
|----------|-----------------|
| `product_search` | "Do you have wireless headphones?", "Compare speakers" |
| `order_tracking` | "Where is my order?", "Tracking number for ORD-12345" |
| `return_refund` | "I want to return this item", "Refund request" |
| `recommendation` | "What laptop do you recommend?", "Gift ideas under $100" |

## Quick Start

```bash
# 1. Setup (auto: venv + deps + .env)
bash setup.sh        # Linux / macOS
.\setup.ps1          # Windows

# 2. Configure
# Edit .env and add your API key

# 3. Run
python -m ecommerce_assistant --query "Do you have wireless headphones?"
```

## Usage

```bash
# Interactive mode (default)
python -m ecommerce_assistant

# Single query
python -m ecommerce_assistant --query "Where is my order ORD-12345?"

# Classify only (no specialist response)
python -m ecommerce_assistant --query "I want a refund" --classify-only

# Batch mode
python -m ecommerce_assistant --file queries.txt
```

## Project Structure

```
ecommerce-assistant/
├── src/ecommerce_assistant/
│   ├── __init__.py
│   ├── __main__.py          # python -m entry point
│   ├── main.py              # CLI with 3 modes
│   ├── crew.py              # Agent/Task/Crew definitions
│   ├── config/
│   │   ├── agents.yaml      # Agent roles & backstories
│   │   └── tasks.yaml       # Task descriptions & expected outputs
│   ├── knowledge/
│   │   └── product_catalog.md  # Sample product data (replaceable)
│   └── tools/
│       ├── __init__.py
│       └── custom_tool.py   # search_product_catalog, lookup_order
├── tests/
│   └── test_crew.py         # Full test suite (mocked, no API keys)
├── .env.example              # Template environment config
├── pyproject.toml            # Project metadata & deps
├── setup.sh / setup.ps1      # One-click setup scripts
└── README.md
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MODEL` | `gpt-4o` | Main LLM for specialist agents |
| `CLASSIFIER_MODEL` | `gpt-4o-mini` | Cheaper model for classification |
| `OPENAI_API_KEY` | — | Your OpenAI API key |
| `VERBOSE` | `true` | Show agent reasoning in console |
| `LOG_LEVEL` | `INFO` | Logging verbosity |

### Customization

1. **Products**: Edit `src/ecommerce_assistant/knowledge/product_catalog.md`
2. **Agent behavior**: Edit `src/ecommerce_assistant/config/agents.yaml`
3. **Task prompts**: Edit `src/ecommerce_assistant/config/tasks.yaml`
4. **Tools**: Add real backends in `src/ecommerce_assistant/tools/custom_tool.py`

## Testing

```bash
# Run all tests
pytest -v

# Run with coverage
pytest --cov=ecommerce_assistant -v
```

All tests are fully mocked — **no API keys or LLM calls required**.

## Extending

### Connect to a Real Product Database

Replace the keyword-based search in `tools/custom_tool.py` with:
- **Elasticsearch** / **Algolia** for full-text product search
- **PostgreSQL** / **MongoDB** for structured product queries
- **Vector DB** (ChromaDB, Pinecone) for semantic product search

### Connect to a Real Order System

Replace the sample data in `lookup_order` with:
- **Shopify API** / **WooCommerce API**
- **Your own order management REST API**
- **Database queries** to your order table

## License

[Apache 2.0](LICENSE)
