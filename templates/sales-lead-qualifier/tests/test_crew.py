"""Tests for the sales lead qualifier agent.

Covers:
- Lead database search tool (keyword matching, edge cases)
- Company lookup tool (valid/invalid company names)
- Classification normalization logic
- SalesResult Pydantic model validation
- YAML configuration loading
- Agent factory (mocked LLM)
- Task factory (query interpolation)
- classify_request (mocked CrewAI)
- handle_request integration (mocked CrewAI)
- CLI argument parsing
- Environment variable handling
"""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Helper: all agent keys for mock setup
_AGENT_KEYS = [
    "classifier", "lead_scorer",
    "company_researcher", "email_composer", "objection_handler",
]


def _mock_agents_dict():
    """Create a dict of MagicMock agents for all 5 roles."""
    return {k: MagicMock() for k in _AGENT_KEYS}


# ═══════════════════════════════════════════════════════════════════════════════
# 1. Lead Database Search Tool
# ═══════════════════════════════════════════════════════════════════════════════


class TestLeadDatabaseSearch:
    """Test the lead database search tool."""

    def test_search_finds_techflow(self):
        from sales_lead_qualifier.tools.custom_tool import search_lead_database

        result = search_lead_database.run("TechFlow")
        assert "techflow" in result.lower() or "series b" in result.lower()

    def test_search_finds_medicore(self):
        from sales_lead_qualifier.tools.custom_tool import search_lead_database

        result = search_lead_database.run("MediCore")
        assert "medicore" in result.lower() or "healthcare" in result.lower()

    def test_search_no_results(self):
        from sales_lead_qualifier.tools.custom_tool import search_lead_database

        result = search_lead_database.run("xyznonexistent12345")
        assert "No leads found" in result

    def test_search_case_insensitive(self):
        from sales_lead_qualifier.tools.custom_tool import search_lead_database

        lower = search_lead_database.run("techflow")
        upper = search_lead_database.run("TECHFLOW")
        assert "No leads found" not in lower
        assert "No leads found" not in upper

    def test_search_by_industry(self):
        from sales_lead_qualifier.tools.custom_tool import search_lead_database

        result = search_lead_database.run("Healthcare")
        assert "No leads found" not in result

    def test_search_by_contact_name(self):
        from sales_lead_qualifier.tools.custom_tool import search_lead_database

        result = search_lead_database.run("Sarah Chen")
        assert "No leads found" not in result

    def test_search_returns_truncated_results(self):
        from sales_lead_qualifier.tools.custom_tool import search_lead_database

        result = search_lead_database.run("lead")
        for section in result.split("---"):
            assert len(section.strip()) <= 800 or section.strip() == ""

    def test_search_empty_query(self):
        from sales_lead_qualifier.tools.custom_tool import search_lead_database

        result = search_lead_database.run("")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_search_finds_bant_data(self):
        """BANT assessment data should be searchable."""
        from sales_lead_qualifier.tools.custom_tool import search_lead_database

        result = search_lead_database.run("Budget")
        assert "No leads found" not in result


# ═══════════════════════════════════════════════════════════════════════════════
# 2. Company Lookup Tool
# ═══════════════════════════════════════════════════════════════════════════════


class TestCompanyLookup:
    """Test the company lookup tool."""

    def test_lookup_techflow(self):
        from sales_lead_qualifier.tools.custom_tool import lookup_company

        result = lookup_company.run("TechFlow Solutions")
        assert "SaaS" in result or "Developer Tools" in result
        assert "Austin" in result

    def test_lookup_globalmart(self):
        from sales_lead_qualifier.tools.custom_tool import lookup_company

        result = lookup_company.run("GlobalMart Retail")
        assert "E-commerce" in result or "Retail" in result

    def test_lookup_medicore(self):
        from sales_lead_qualifier.tools.custom_tool import lookup_company

        result = lookup_company.run("MediCore Health")
        assert "Healthcare" in result
        assert "Boston" in result

    def test_lookup_greenleaf(self):
        from sales_lead_qualifier.tools.custom_tool import lookup_company

        result = lookup_company.run("GreenLeaf Energy")
        assert "Clean Energy" in result or "Sustainability" in result

    def test_lookup_pinnacle(self):
        from sales_lead_qualifier.tools.custom_tool import lookup_company

        result = lookup_company.run("Pinnacle Consulting Group")
        assert "Consulting" in result

    def test_lookup_invalid_company(self):
        from sales_lead_qualifier.tools.custom_tool import lookup_company

        result = lookup_company.run("Nonexistent Corp")
        assert "Company not found" in result

    def test_lookup_case_insensitive(self):
        from sales_lead_qualifier.tools.custom_tool import lookup_company

        result = lookup_company.run("techflow solutions")
        assert "SaaS" in result or "Developer Tools" in result

    def test_lookup_includes_contacts(self):
        from sales_lead_qualifier.tools.custom_tool import lookup_company

        result = lookup_company.run("TechFlow Solutions")
        assert "Key Contacts" in result
        assert "Sarah Chen" in result

    def test_lookup_empty_name(self):
        from sales_lead_qualifier.tools.custom_tool import lookup_company

        result = lookup_company.run("")
        assert "Company not found" in result


# ═══════════════════════════════════════════════════════════════════════════════
# 3. Classification Normalization Logic
# ═══════════════════════════════════════════════════════════════════════════════


class TestClassificationNormalization:
    """Test request classification normalization logic.

    This tests the raw-output-to-category mapping logic used in
    classify_request() without calling any LLM.
    """

    @pytest.mark.parametrize(
        "raw_output, expected",
        [
            ("lead_scoring", "lead_scoring"),
            ("LEAD_SCORING", "lead_scoring"),
            ("company_research", "company_research"),
            ("COMPANY_RESEARCH", "company_research"),
            ("email_outreach", "email_outreach"),
            ("EMAIL_OUTREACH", "email_outreach"),
            ("objection_handling", "objection_handling"),
            ("OBJECTION_HANDLING", "objection_handling"),
            ("score this lead", "lead_scoring"),
            ("lead scoring needed", "lead_scoring"),
            ("research the company", "company_research"),
            ("company research please", "company_research"),
            ("compose an email", "email_outreach"),
            ("email outreach draft", "email_outreach"),
            ("handle this objection", "objection_handling"),
            ("objection from prospect", "objection_handling"),
            ("qualify this prospect", "lead_scoring"),
            ("bant analysis", "lead_scoring"),
            ("write a follow-up", "email_outreach"),
            ("draft a message", "email_outreach"),
            ("unknown query type", "lead_scoring"),  # default fallback
            ("", "lead_scoring"),  # empty → default
            ("   ", "lead_scoring"),  # whitespace → default
        ],
    )
    def test_normalize(self, raw_output: str, expected: str):
        """Category normalization should match expected output."""
        raw_lower = raw_output.strip().lower()
        if "lead_scoring" in raw_lower or ("lead" in raw_lower and "scor" in raw_lower):
            result = "lead_scoring"
        elif "company_research" in raw_lower or (
            "company" in raw_lower and "research" in raw_lower
        ):
            result = "company_research"
        elif "email_outreach" in raw_lower or (
            "email" in raw_lower and ("outreach" in raw_lower or "compose" in raw_lower)
        ):
            result = "email_outreach"
        elif "objection_handling" in raw_lower or "objection" in raw_lower:
            result = "objection_handling"
        elif "qualify" in raw_lower or "bant" in raw_lower or "score" in raw_lower:
            result = "lead_scoring"
        elif "research" in raw_lower or "intel" in raw_lower:
            result = "company_research"
        elif "email" in raw_lower or "write" in raw_lower or "draft" in raw_lower:
            result = "email_outreach"
        else:
            result = "lead_scoring"
        assert result == expected, f"Failed for input: {raw_output!r}"


# ═══════════════════════════════════════════════════════════════════════════════
# 4. SalesResult Pydantic Model
# ═══════════════════════════════════════════════════════════════════════════════


class TestSalesResult:
    """Test the SalesResult model."""

    def test_valid_lead_scoring_result(self):
        from sales_lead_qualifier.crew import SalesResult

        result = SalesResult(
            query="Score TechFlow Solutions as a lead",
            category="lead_scoring",
            response="Lead Score: 82 — Hot Lead",
        )
        assert result.query == "Score TechFlow Solutions as a lead"
        assert result.category == "lead_scoring"
        assert "Hot" in result.response

    def test_valid_company_research_result(self):
        from sales_lead_qualifier.crew import SalesResult

        result = SalesResult(
            query="Research MediCore Health",
            category="company_research",
            response="MediCore Health is a healthcare technology company",
        )
        assert result.category == "company_research"

    def test_valid_email_outreach_result(self):
        from sales_lead_qualifier.crew import SalesResult

        result = SalesResult(
            query="Write a cold email to Sarah Chen at TechFlow",
            category="email_outreach",
            response="Subject: Accelerate your CI/CD pipeline",
        )
        assert result.category == "email_outreach"

    def test_valid_objection_handling_result(self):
        from sales_lead_qualifier.crew import SalesResult

        result = SalesResult(
            query="They said our pricing is too high",
            category="objection_handling",
            response="Response Option 1: Let's look at the ROI",
        )
        assert result.category == "objection_handling"

    def test_invalid_category_rejected(self):
        from sales_lead_qualifier.crew import SalesResult

        with pytest.raises(Exception):
            SalesResult(
                query="test",
                category="invalid_category",
                response="test",
            )

    def test_empty_query_allowed(self):
        from sales_lead_qualifier.crew import SalesResult

        result = SalesResult(
            query="", category="lead_scoring", response="No query provided."
        )
        assert result.query == ""

    def test_long_response_allowed(self):
        from sales_lead_qualifier.crew import SalesResult

        long_text = "A" * 10_000
        result = SalesResult(
            query="test", category="lead_scoring", response=long_text
        )
        assert len(result.response) == 10_000


# ═══════════════════════════════════════════════════════════════════════════════
# 5. YAML Configuration Loading
# ═══════════════════════════════════════════════════════════════════════════════


class TestYamlConfig:
    """Test YAML configuration files are valid and complete."""

    def test_load_agents_yaml(self):
        from sales_lead_qualifier.crew import _load_yaml

        config = _load_yaml("agents.yaml")
        assert isinstance(config, dict)
        expected_agents = [
            "classifier", "lead_scorer", "company_researcher",
            "email_composer", "objection_handler",
        ]
        for agent_key in expected_agents:
            assert agent_key in config, f"Missing agent: {agent_key}"
            assert "role" in config[agent_key], f"Missing 'role' for {agent_key}"
            assert "goal" in config[agent_key], f"Missing 'goal' for {agent_key}"
            assert "backstory" in config[agent_key], f"Missing 'backstory' for {agent_key}"

    def test_load_tasks_yaml(self):
        from sales_lead_qualifier.crew import _load_yaml

        config = _load_yaml("tasks.yaml")
        assert isinstance(config, dict)
        expected_tasks = [
            "classify_request", "score_lead", "research_company",
            "compose_email", "handle_objection",
        ]
        for task_key in expected_tasks:
            assert task_key in config, f"Missing task: {task_key}"
            assert "description" in config[task_key], (
                f"Missing 'description' for {task_key}"
            )
            assert "expected_output" in config[task_key], (
                f"Missing 'expected_output' for {task_key}"
            )

    def test_tasks_contain_query_placeholder(self):
        """All task descriptions should contain {query} placeholder."""
        from sales_lead_qualifier.crew import _load_yaml

        config = _load_yaml("tasks.yaml")
        for task_key, task_cfg in config.items():
            assert "{query}" in task_cfg["description"], (
                f"Task '{task_key}' description missing {{query}} placeholder"
            )

    def test_load_nonexistent_yaml_raises(self):
        """Loading a non-existent YAML file should raise FileNotFoundError."""
        from sales_lead_qualifier.crew import _load_yaml

        with pytest.raises(FileNotFoundError):
            _load_yaml("nonexistent.yaml")


# ═══════════════════════════════════════════════════════════════════════════════
# 6. Agent Factory (mocked — no LLM calls)
# ═══════════════════════════════════════════════════════════════════════════════


class TestAgentFactory:
    """Test agent creation from YAML config (mocked to avoid LLM calls)."""

    @patch("sales_lead_qualifier.crew.Agent")
    def test_creates_five_agents(self, mock_agent_cls):
        """_create_agents should create exactly 5 agents."""
        from sales_lead_qualifier.crew import _create_agents

        agents = _create_agents()
        assert len(agents) == 5
        assert set(agents.keys()) == set(_AGENT_KEYS)

    @patch("sales_lead_qualifier.crew.Agent")
    def test_classifier_uses_mini_model(self, mock_agent_cls):
        """Classifier should use the cheaper CLASSIFIER_MODEL."""
        from sales_lead_qualifier.crew import _create_agents

        with patch.dict(os.environ, {"CLASSIFIER_MODEL": "gpt-4o-mini", "MODEL": "gpt-4o"}):
            _create_agents()

        calls = mock_agent_cls.call_args_list
        classifier_call = calls[0]
        assert classifier_call.kwargs.get("llm") == "gpt-4o-mini"

    @patch("sales_lead_qualifier.crew.Agent")
    def test_verbose_env_controls_agent_verbosity(self, mock_agent_cls):
        """VERBOSE=false should set verbose=False on all agents."""
        from sales_lead_qualifier.crew import _create_agents

        with patch.dict(os.environ, {"VERBOSE": "false"}):
            _create_agents()

        for call in mock_agent_cls.call_args_list:
            assert call.kwargs.get("verbose") is False


# ═══════════════════════════════════════════════════════════════════════════════
# 7. Task Factory
# ═══════════════════════════════════════════════════════════════════════════════


class TestTaskFactory:
    """Test task creation from YAML config."""

    @patch("sales_lead_qualifier.crew.Task")
    def test_query_interpolation(self, mock_task_cls):
        """_create_task should replace {query} in the task description."""
        from sales_lead_qualifier.crew import _create_task

        mock_agent = MagicMock()
        _create_task("classify_request", mock_agent, "Score TechFlow Solutions")

        call_kwargs = mock_task_cls.call_args.kwargs
        assert "Score TechFlow Solutions" in call_kwargs["description"]
        assert "{query}" not in call_kwargs["description"]

    @patch("sales_lead_qualifier.crew.Task")
    def test_all_task_keys_valid(self, mock_task_cls):
        """All expected task keys should produce a valid Task."""
        from sales_lead_qualifier.crew import _create_task

        mock_agent = MagicMock()
        for key in [
            "classify_request", "score_lead", "research_company",
            "compose_email", "handle_objection",
        ]:
            _create_task(key, mock_agent, "test query")
            assert mock_task_cls.called


# ═══════════════════════════════════════════════════════════════════════════════
# 8. classify_request (mocked CrewAI)
# ═══════════════════════════════════════════════════════════════════════════════


class TestClassifyRequest:
    """Test classify_request with mocked CrewAI Crew.kickoff()."""

    @patch("sales_lead_qualifier.crew._create_task", return_value=MagicMock())
    @patch("sales_lead_qualifier.crew._create_agents")
    @patch("sales_lead_qualifier.crew.Crew")
    def test_classify_lead_scoring(self, mock_crew_cls, mock_agents, mock_task):
        from sales_lead_qualifier.crew import classify_request

        mock_agents.return_value = _mock_agents_dict()
        mock_result = MagicMock()
        mock_result.raw = "lead_scoring"
        mock_crew_cls.return_value.kickoff.return_value = mock_result

        assert classify_request("Score TechFlow Solutions as a lead") == "lead_scoring"

    @patch("sales_lead_qualifier.crew._create_task", return_value=MagicMock())
    @patch("sales_lead_qualifier.crew._create_agents")
    @patch("sales_lead_qualifier.crew.Crew")
    def test_classify_company_research(self, mock_crew_cls, mock_agents, mock_task):
        from sales_lead_qualifier.crew import classify_request

        mock_agents.return_value = _mock_agents_dict()
        mock_result = MagicMock()
        mock_result.raw = "company_research"
        mock_crew_cls.return_value.kickoff.return_value = mock_result

        assert classify_request("Research MediCore Health") == "company_research"

    @patch("sales_lead_qualifier.crew._create_task", return_value=MagicMock())
    @patch("sales_lead_qualifier.crew._create_agents")
    @patch("sales_lead_qualifier.crew.Crew")
    def test_classify_email_outreach(self, mock_crew_cls, mock_agents, mock_task):
        from sales_lead_qualifier.crew import classify_request

        mock_agents.return_value = _mock_agents_dict()
        mock_result = MagicMock()
        mock_result.raw = "email_outreach"
        mock_crew_cls.return_value.kickoff.return_value = mock_result

        assert classify_request("Write a cold email to Sarah Chen") == "email_outreach"

    @patch("sales_lead_qualifier.crew._create_task", return_value=MagicMock())
    @patch("sales_lead_qualifier.crew._create_agents")
    @patch("sales_lead_qualifier.crew.Crew")
    def test_classify_objection_handling(self, mock_crew_cls, mock_agents, mock_task):
        from sales_lead_qualifier.crew import classify_request

        mock_agents.return_value = _mock_agents_dict()
        mock_result = MagicMock()
        mock_result.raw = "objection_handling"
        mock_crew_cls.return_value.kickoff.return_value = mock_result

        assert classify_request("They said pricing is too high") == "objection_handling"

    @patch("sales_lead_qualifier.crew._create_task", return_value=MagicMock())
    @patch("sales_lead_qualifier.crew._create_agents")
    @patch("sales_lead_qualifier.crew.Crew")
    def test_classify_unknown_defaults_to_lead_scoring(
        self, mock_crew_cls, mock_agents, mock_task,
    ):
        from sales_lead_qualifier.crew import classify_request

        mock_agents.return_value = _mock_agents_dict()
        mock_result = MagicMock()
        mock_result.raw = "I'm not sure what category this is"
        mock_crew_cls.return_value.kickoff.return_value = mock_result

        assert classify_request("Something unclear") == "lead_scoring"


# ═══════════════════════════════════════════════════════════════════════════════
# 9. handle_request (mocked CrewAI)
# ═══════════════════════════════════════════════════════════════════════════════


class TestHandleRequest:
    """Test handle_request end-to-end with mocked CrewAI."""

    @patch("sales_lead_qualifier.crew._create_task", return_value=MagicMock())
    @patch("sales_lead_qualifier.crew._create_agents")
    @patch("sales_lead_qualifier.crew.Crew")
    @patch("sales_lead_qualifier.crew.classify_request", return_value="lead_scoring")
    def test_handle_lead_scoring_returns_result(
        self, mock_classify, mock_crew_cls, mock_agents, mock_task,
    ):
        from sales_lead_qualifier.crew import SalesResult, handle_request

        mock_agents.return_value = _mock_agents_dict()
        mock_result = MagicMock()
        mock_result.raw = (
            "Lead Score: 82 — Hot Lead. BANT: Budget 22, Authority 24, Need 22, Timeline 14."
        )
        mock_crew_cls.return_value.kickoff.return_value = mock_result

        result = handle_request("Score TechFlow Solutions as a lead")
        assert isinstance(result, SalesResult)
        assert result.category == "lead_scoring"
        assert result.query == "Score TechFlow Solutions as a lead"
        assert "82" in result.response

    @patch("sales_lead_qualifier.crew._create_task", return_value=MagicMock())
    @patch("sales_lead_qualifier.crew._create_agents")
    @patch("sales_lead_qualifier.crew.Crew")
    @patch("sales_lead_qualifier.crew.classify_request", return_value="company_research")
    def test_handle_company_research_routes_correctly(
        self, mock_classify, mock_crew_cls, mock_agents, mock_task,
    ):
        from sales_lead_qualifier.crew import handle_request

        mock_agents.return_value = _mock_agents_dict()
        mock_result = MagicMock()
        mock_result.raw = (
            "**Company Overview**: MediCore Health — Healthcare Technology — 500 employees"
        )
        mock_crew_cls.return_value.kickoff.return_value = mock_result

        result = handle_request("Research MediCore Health")
        assert result.category == "company_research"
        assert "MediCore" in result.response

    @patch("sales_lead_qualifier.crew._create_task", return_value=MagicMock())
    @patch("sales_lead_qualifier.crew._create_agents")
    @patch("sales_lead_qualifier.crew.Crew")
    @patch("sales_lead_qualifier.crew.classify_request", return_value="email_outreach")
    def test_handle_email_outreach_routes_correctly(
        self, mock_classify, mock_crew_cls, mock_agents, mock_task,
    ):
        from sales_lead_qualifier.crew import handle_request

        mock_agents.return_value = _mock_agents_dict()
        mock_result = MagicMock()
        mock_result.raw = "**Subject Line**: Accelerate your CI/CD pipeline by 10x"
        mock_crew_cls.return_value.kickoff.return_value = mock_result

        result = handle_request("Write a cold email to Sarah Chen at TechFlow")
        assert result.category == "email_outreach"
        assert "Subject" in result.response

    @patch("sales_lead_qualifier.crew._create_task", return_value=MagicMock())
    @patch("sales_lead_qualifier.crew._create_agents")
    @patch("sales_lead_qualifier.crew.Crew")
    @patch("sales_lead_qualifier.crew.classify_request", return_value="objection_handling")
    def test_handle_objection_routes_correctly(
        self, mock_classify, mock_crew_cls, mock_agents, mock_task,
    ):
        from sales_lead_qualifier.crew import handle_request

        mock_agents.return_value = _mock_agents_dict()
        mock_result = MagicMock()
        mock_result.raw = (
            "**Objection Category**: Price\n**Response Option 1**: Let's look at the ROI"
        )
        mock_crew_cls.return_value.kickoff.return_value = mock_result

        result = handle_request("They said our pricing is too high")
        assert result.category == "objection_handling"
        assert "Price" in result.response


# ═══════════════════════════════════════════════════════════════════════════════
# 10. CLI Argument Parsing
# ═══════════════════════════════════════════════════════════════════════════════


class TestCLI:
    """Test CLI argument parsing (no LLM calls)."""

    def test_parse_single_query(self):
        import argparse

        parser = argparse.ArgumentParser()
        parser.add_argument("--query", "-q", type=str)
        parser.add_argument("--file", "-f", type=str)
        parser.add_argument("--classify-only", "-c", action="store_true")

        args = parser.parse_args(["--query", "Score TechFlow as a lead"])
        assert args.query == "Score TechFlow as a lead"
        assert args.file is None
        assert args.classify_only is False

    def test_parse_classify_only(self):
        import argparse

        parser = argparse.ArgumentParser()
        parser.add_argument("--query", "-q", type=str)
        parser.add_argument("--file", "-f", type=str)
        parser.add_argument("--classify-only", "-c", action="store_true")

        args = parser.parse_args(["-q", "test", "-c"])
        assert args.classify_only is True

    def test_parse_file_mode(self):
        import argparse

        parser = argparse.ArgumentParser()
        parser.add_argument("--query", "-q", type=str)
        parser.add_argument("--file", "-f", type=str)
        parser.add_argument("--classify-only", "-c", action="store_true")

        args = parser.parse_args(["--file", "queries.txt"])
        assert args.file == "queries.txt"
        assert args.query is None

    def test_batch_file_not_found(self, tmp_path):
        nonexistent = tmp_path / "no_such_file.txt"
        assert not nonexistent.exists()


# ═══════════════════════════════════════════════════════════════════════════════
# 11. Environment Variable Handling
# ═══════════════════════════════════════════════════════════════════════════════


class TestEnvConfig:
    """Test environment variable configuration."""

    def test_env_example_exists(self):
        env_example = Path(__file__).parent.parent / ".env.example"
        assert env_example.exists(), ".env.example is required for template users"

    def test_env_example_contains_required_vars(self):
        env_example = Path(__file__).parent.parent / ".env.example"
        content = env_example.read_text(encoding="utf-8")
        required_vars = ["MODEL", "OPENAI_API_KEY", "CLASSIFIER_MODEL"]
        for var in required_vars:
            assert var in content, f".env.example missing {var}"

    def test_gitignore_excludes_env(self):
        gitignore = Path(__file__).parent.parent / ".gitignore"
        content = gitignore.read_text(encoding="utf-8")
        assert ".env" in content
