# 📝 Content Marketing Agent

> AI-powered content marketing agent that plans content strategy, writes blog posts, creates social media content, and analyzes SEO.

## Features

| Category            | What it does                                                     |
| ------------------- | ---------------------------------------------------------------- |
| 📋 Content Strategy | Plan editorial calendars, define content pillars, build personas |
| ✍️ Blog Writing     | Write blog outlines, articles, thought leadership, how-to guides |
| 📱 Social Media     | Create platform-specific posts, captions, hashtag strategies     |
| 🔍 SEO Analysis     | Research keywords, audit on-page SEO, analyze search rankings    |

## Agents

| Agent                | Role                           | Tools                                |
| -------------------- | ------------------------------ | ------------------------------------ |
| Classifier           | Routes requests to specialists | —                                    |
| Content Strategist   | Content planning & editorial   | Content Guide, Campaign, Performance |
| Blog Writer          | Blog post creation             | Content Guide, Campaign              |
| Social Media Creator | Platform-specific content      | Content Guide, Performance           |
| SEO Analyzer         | Keyword & search optimization  | Content Guide, Performance           |

## Quick Start

```bash
# 1. Setup (auto: venv + deps + .env)
bash setup.sh        # Linux / macOS
.\setup.ps1          # Windows

# 2. Configure
# Edit .env and add your API key

# 3. Run
python -m content_marketing --query "Write a blog post about AI trends in 2026"
```

## Usage

```bash
# Interactive mode
python -m content_marketing

# Single query
python -m content_marketing --query "Create a LinkedIn carousel about our product launch"

# Classify only (no full response)
python -m content_marketing --query "Research keywords for content marketing" --classify-only

# Batch mode
python -m content_marketing --file requests.txt
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
- **`knowledge/content_marketing_guide.md`** — Content marketing best practices and guidelines

## Project Structure

```
content-marketing/
├── pyproject.toml
├── setup.sh / setup.ps1
├── .env.example
├── src/
│   └── content_marketing/
│       ├── main.py              # CLI entry point
│       ├── crew.py              # Agent & task definitions
│       ├── config/
│       │   ├── agents.yaml      # Agent configuration
│       │   └── tasks.yaml       # Task configuration
│       ├── tools/
│       │   └── custom_tool.py   # Guide search, campaign lookup, performance
│       └── knowledge/
│           └── content_marketing_guide.md  # Strategy, writing, SEO best practices
└── tests/
    └── test_crew.py             # 112 tests (all mocked)
```

## Testing

```bash
pip install -e ".[dev]"
pytest -v  # 112 tests, all mocked — no API keys needed
```

## Extending

### Add a new category

1. Add agent definition to `config/agents.yaml`
2. Add task definition to `config/tasks.yaml`
3. Add the category to `ContentResult.category` Literal type in `crew.py`
4. Add routing entry to `task_map` in `handle_request()`
5. Add normalization rules to `_normalize_category()`
6. Add knowledge base articles to `knowledge/content_marketing_guide.md`

### Add custom tools

1. Create a new `@tool` function in `tools/custom_tool.py`
2. Import and assign to the relevant agent in `_create_agents()`

### Connect to real systems

Replace the sample data in `tools/custom_tool.py` with your actual integrations:

- **CMS**: WordPress REST API, Contentful, Strapi
- **SEO tools**: Ahrefs API, SEMrush API, Google Search Console
- **Social platforms**: LinkedIn API, Twitter/X API, Meta Graph API
- **Analytics**: Google Analytics 4, Mixpanel, Amplitude
- **Email**: Mailchimp API, HubSpot API, SendGrid

## License

Apache 2.0 — see [LICENSE](LICENSE).
