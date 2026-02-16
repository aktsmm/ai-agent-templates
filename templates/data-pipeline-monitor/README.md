# 📊 Data Pipeline Monitor

> AI-powered data pipeline monitoring agent that checks pipeline health, analyzes data quality, manages alerts, and recommends recovery actions.

## Features

| Category            | What it does                                              |
| ------------------- | --------------------------------------------------------- |
| 🔄 Pipeline Health  | Monitor execution status, latency, throughput, scheduling |
| 🔍 Data Quality     | Check completeness, freshness, schema drift, anomalies    |
| 🔔 Alert Management | Configure alerts, routing, escalation, notifications      |
| 🔧 Recovery         | Recommend retry strategies, rollback, backfill procedures |

## Agents

| Agent                   | Role                             | Tools                    |
| ----------------------- | -------------------------------- | ------------------------ |
| Classifier              | Routes requests to specialists   | —                        |
| Pipeline Health Checker | Execution status & performance   | Pipeline Status, Runbook |
| Data Quality Analyzer   | Data quality metrics & issues    | Data Metrics, Runbook    |
| Alert Manager           | Alert configuration & escalation | Runbook                  |
| Recovery Advisor        | Recovery actions & remediation   | Pipeline Status, Runbook |

## Quick Start

```bash
# 1. Setup (auto: venv + deps + .env)
bash setup.sh        # Linux / macOS
.\setup.ps1          # Windows

# 2. Configure
# Edit .env and add your API key

# 3. Run
python -m data_pipeline_monitor --query "ETL-003 failed with connection error"
```

## Usage

```bash
# Interactive mode
python -m data_pipeline_monitor

# Single query
python -m data_pipeline_monitor --query "Check data quality for the customers dataset"

# Classify only (no full response)
python -m data_pipeline_monitor --query "Set up PagerDuty alerts for pipeline failures" --classify-only

# Batch mode
python -m data_pipeline_monitor --file requests.txt
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
- **`knowledge/data_pipeline_runbook.md`** — Operational runbook and procedures

## Project Structure

```
data-pipeline-monitor/
├── pyproject.toml
├── setup.sh / setup.ps1
├── .env.example
├── src/
│   └── data_pipeline_monitor/
│       ├── main.py              # CLI entry point
│       ├── crew.py              # Agent & task definitions
│       ├── config/
│       │   ├── agents.yaml      # Agent configuration
│       │   └── tasks.yaml       # Task configuration
│       ├── tools/
│       │   └── custom_tool.py   # Pipeline status, data metrics, runbook search
│       └── knowledge/
│           └── data_pipeline_runbook.md  # Operational runbook
└── tests/
    └── test_crew.py             # Unit tests (all mocked)
```

## Testing

```bash
pip install -e ".[dev]"
pytest -v
```

## Extending

### Add a new category

1. Add agent definition to `config/agents.yaml`
2. Add task definition to `config/tasks.yaml`
3. Add the category to `DataPipelineResult.category` Literal type in `crew.py`
4. Add routing entry to `task_map` in `handle_request()`
5. Add normalization rules to `_normalize_category()`
6. Add runbook sections to `knowledge/data_pipeline_runbook.md`

### Add custom tools

1. Create a new `@tool` function in `tools/custom_tool.py`
2. Import and assign to the relevant agent in `_create_agents()`

### Connect to real systems

Replace the sample data in `tools/custom_tool.py` with your actual integrations:

- **Pipeline orchestrator**: Apache Airflow API, Dagster GraphQL, Prefect API
- **Data quality**: Great Expectations, Monte Carlo, dbt test results
- **Alerting**: PagerDuty, Opsgenie, Slack Webhooks
- **Data warehouse**: Snowflake, BigQuery, Redshift metadata queries

## License

Apache 2.0 — see [LICENSE](LICENSE).
