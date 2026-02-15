# ⚖️ Legal Document Analyzer Agent Template

> AI-powered legal document analyzer using CrewAI. Extracts clauses,
> analyzes risks, summarizes contracts, and compares documents — all with
> multi-agent orchestration.

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![CrewAI](https://img.shields.io/badge/CrewAI-1.9%2B-green.svg)](https://github.com/crewAIInc/crewAI)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-passing-brightgreen.svg)](#testing)

## Features

- **Multi-Agent Architecture** — Classifier routes to 4 specialized legal analysts
- **YAML-Driven Configuration** — Customize agents & tasks without touching code
- **Multiple LLM Providers** — OpenAI, Azure OpenAI, Anthropic, Ollama (local)
- **3 CLI Modes** — Interactive, single query, batch processing
- **Sample Legal Documents** — NDA and Software License Agreement included
- **3 Custom Tools** — Clause search, section overview, cross-document comparison
- **Comprehensive Tests** — Full test suite with mocked LLM calls

## How It Works

```
Analysis Request → Classifier Agent → [Clause Extraction / Risk Analysis / Summarization / Comparison] specialist
```

### Agent Roles

| Agent               | Role                                                   | Tools                                            |
| ------------------- | ------------------------------------------------------ | ------------------------------------------------ |
| **Classifier**      | Routes requests to the right specialist                | —                                                |
| **Clause Extractor**| Finds and presents specific contract clauses           | `search_document_clauses`, `get_document_sections` |
| **Risk Analyzer**   | Identifies legal risks and unfavorable terms           | `search_document_clauses`, `get_document_sections` |
| **Summarizer**      | Creates concise, business-friendly summaries           | `search_document_clauses`, `get_document_sections` |
| **Comparator**      | Compares documents and finds material differences      | `compare_document_sections`, `get_document_sections` |

### Categories

| Category           | Trigger Examples                                                   |
| ------------------ | ------------------------------------------------------------------ |
| `clause_extraction`| "Find the indemnification clause", "Extract termination provisions"|
| `risk_analysis`    | "What are the risks?", "Flag unfavorable terms"                    |
| `summarization`    | "Summarize this NDA", "Give me an overview of the contract"        |
| `comparison`       | "Compare these two agreements", "What changed between versions?"   |

## Quick Start

```bash
# 1. Setup (auto: venv + deps + .env)
bash setup.sh        # Linux / macOS
.\setup.ps1          # Windows

# 2. Configure
# Edit .env and add your API key

# 3. Run
python -m legal_document_analyzer --query "Summarize the NDA"
```

## Usage

```bash
# Interactive mode (default)
python -m legal_document_analyzer

# Single query
python -m legal_document_analyzer --query "Find the indemnification clause in the NDA"

# Classify only (no specialist response)
python -m legal_document_analyzer --query "What are the risks?" --classify-only

# Batch mode
python -m legal_document_analyzer --file queries.txt
```

## Project Structure

```
legal-document-analyzer/
├── src/legal_document_analyzer/
│   ├── __init__.py
│   ├── __main__.py          # python -m entry point
│   ├── main.py              # CLI with 3 modes
│   ├── crew.py              # Agent/Task/Crew definitions
│   ├── config/
│   │   ├── agents.yaml      # Agent roles & backstories
│   │   └── tasks.yaml       # Task descriptions & expected outputs
│   ├── knowledge/
│   │   ├── nda_template.md         # Sample NDA (15 sections)
│   │   └── software_license.md     # Sample License Agreement (15 sections)
│   └── tools/
│       ├── __init__.py
│       └── custom_tool.py   # search_document_clauses, get_document_sections, compare_document_sections
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

1. **Documents**: Add your own contracts to `src/legal_document_analyzer/knowledge/` as Markdown files
2. **Agent behavior**: Edit `src/legal_document_analyzer/config/agents.yaml`
3. **Task prompts**: Edit `src/legal_document_analyzer/config/tasks.yaml`
4. **Tools**: Add real backends in `src/legal_document_analyzer/tools/custom_tool.py`

## Sample Documents Included

### NDA Template (`nda_template.md`)
A mutual Non-Disclosure Agreement with 15 sections including definitions, obligations, exclusions, term, remedies, indemnification, limitation of liability, and governing law.

### Software License Agreement (`software_license.md`)
An enterprise software license agreement with 15 sections covering license grant, restrictions, fees, IP, warranties, liability, support, and data protection.

## Testing

```bash
# Run all tests
pytest -v

# Run with coverage
pytest --cov=legal_document_analyzer -v
```

All tests are fully mocked — **no API keys or LLM calls required**.

## Extending

### Add Your Own Documents

Drop Markdown files into `knowledge/`. The tools automatically discover and index all `.md` files:

```markdown
# My Contract Title

## 1. Definitions
...

## 2. Obligations
...
```

### Connect to a Real Document Store

Replace the file-based search in `tools/custom_tool.py` with:

- **Elasticsearch** / **Azure AI Search** for full-text contract search
- **Vector DB** (ChromaDB, Pinecone) for semantic clause search
- **Document Intelligence** (Azure Form Recognizer) for PDF/scanned document extraction

### Add PDF Support

Extend the tools to handle PDF input:

- **PyPDF2** / **pdfplumber** for text-based PDFs
- **Azure Document Intelligence** for scanned documents with OCR
- **Unstructured.io** for multi-format document parsing

## License

[MIT](LICENSE)
