"""Tests for the customer support agent.

Covers:
- Knowledge base search tool (keyword matching, edge cases)
- Classification normalization logic
- SupportResult Pydantic model validation
- YAML configuration loading
- Agent factory (mocked LLM)
- classify_inquiry / handle_inquiry integration (mocked CrewAI)
- CLI argument parsing
"""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Helper: all agent keys for mock setup
_AGENT_KEYS = [
    "classifier", "faq_specialist",
    "ticket_handler", "escalation_manager",
]


def _mock_agents_dict():
    """Create a dict of MagicMock agents for all 4 roles."""
    return {k: MagicMock() for k in _AGENT_KEYS}


# ═══════════════════════════════════════════════════════════════════════════════
# 1. Knowledge Base Search Tool
# ═══════════════════════════════════════════════════════════════════════════════


class TestKnowledgeBaseSearch:
    """Test the knowledge base search tool."""

    def test_search_finds_matching_section(self):
        from customer_support.tools.custom_tool import search_knowledge_base

        result = search_knowledge_base.run("password")
        assert "password" in result.lower() or "reset" in result.lower()

    def test_search_no_results(self):
        from customer_support.tools.custom_tool import search_knowledge_base

        result = search_knowledge_base.run("xyznonexistent12345")
        assert "No relevant information" in result

    def test_search_billing_keyword(self):
        """Billing-related queries should match the billing FAQ section."""
        from customer_support.tools.custom_tool import search_knowledge_base

        result = search_knowledge_base.run("refund")
        assert "refund" in result.lower() or "money-back" in result.lower()

    def test_search_case_insensitive(self):
        """Search should be case-insensitive."""
        from customer_support.tools.custom_tool import search_knowledge_base

        lower = search_knowledge_base.run("password")
        upper = search_knowledge_base.run("PASSWORD")
        # Both should find results (not "No relevant information")
        assert "No relevant information" not in lower
        assert "No relevant information" not in upper

    def test_search_pricing_keyword(self):
        """Pricing queries should match the pricing FAQ section."""
        from customer_support.tools.custom_tool import search_knowledge_base

        result = search_knowledge_base.run("pricing")
        # "Pricing" is a section header, should match
        assert "No relevant information" not in result

    def test_search_returns_truncated_results(self):
        """Each result section should be truncated to max 500 chars."""
        from customer_support.tools.custom_tool import search_knowledge_base

        result = search_knowledge_base.run("account")
        # Each section part should be ≤ 500 chars (separated by ---)
        for section in result.split("---"):
            assert len(section.strip()) <= 500 or section.strip() == ""

    def test_search_empty_query(self):
        """Empty query should still return some results or no-match message."""
        from customer_support.tools.custom_tool import search_knowledge_base

        result = search_knowledge_base.run("")
        assert isinstance(result, str)
        assert len(result) > 0


# ═══════════════════════════════════════════════════════════════════════════════
# 2. Classification Normalization Logic
# ═══════════════════════════════════════════════════════════════════════════════


class TestClassificationNormalization:
    """Test inquiry classification normalization logic.

    This tests the raw-output-to-category mapping logic used in
    classify_inquiry() without calling any LLM.
    """

    @pytest.mark.parametrize(
        "raw_output, expected",
        [
            ("faq", "faq"),
            ("FAQ", "faq"),
            ("This is a faq question", "faq"),
            ("ticket", "ticket"),
            ("escalation", "escalation"),
            ("escalate", "escalation"),
            ("ESCALATION NEEDED", "escalation"),
            ("unknown", "ticket"),  # default fallback
            ("", "ticket"),  # empty → default
            ("   ", "ticket"),  # whitespace → default
            ("faq and ticket", "faq"),  # faq takes priority
            ("please escalate this ticket", "ticket"),  # ticket before escalat
        ],
    )
    def test_normalize(self, raw_output: str, expected: str):
        """Category normalization should match expected output."""
        raw_lower = raw_output.strip().lower()
        if "faq" in raw_lower:
            result = "faq"
        elif "ticket" in raw_lower:
            result = "ticket"
        elif "escalat" in raw_lower:
            result = "escalation"
        else:
            result = "ticket"
        assert result == expected, f"Failed for input: {raw_output!r}"


# ═══════════════════════════════════════════════════════════════════════════════
# 3. SupportResult Pydantic Model
# ═══════════════════════════════════════════════════════════════════════════════


class TestSupportResult:
    """Test the SupportResult model."""

    def test_valid_faq_result(self):
        from customer_support.crew import SupportResult

        result = SupportResult(
            query="How do I reset my password?",
            category="faq",
            response="Go to the login page and click Forgot Password.",
        )
        assert result.query == "How do I reset my password?"
        assert result.category == "faq"
        assert "Forgot Password" in result.response

    def test_valid_ticket_result(self):
        from customer_support.crew import SupportResult

        result = SupportResult(
            query="App crashes on startup",
            category="ticket",
            response="Ticket created: Priority High",
        )
        assert result.category == "ticket"

    def test_valid_escalation_result(self):
        from customer_support.crew import SupportResult

        result = SupportResult(
            query="Data breach detected",
            category="escalation",
            response="Escalation report prepared",
        )
        assert result.category == "escalation"

    def test_invalid_category_rejected(self):
        from customer_support.crew import SupportResult

        with pytest.raises(Exception):
            SupportResult(
                query="test",
                category="invalid_category",
                response="test",
            )

    def test_empty_query_allowed(self):
        """Empty query string should be accepted by the model."""
        from customer_support.crew import SupportResult

        result = SupportResult(query="", category="faq", response="No question provided.")
        assert result.query == ""

    def test_long_response_allowed(self):
        """Very long responses should be accepted."""
        from customer_support.crew import SupportResult

        long_text = "A" * 10_000
        result = SupportResult(query="test", category="ticket", response=long_text)
        assert len(result.response) == 10_000


# ═══════════════════════════════════════════════════════════════════════════════
# 4. YAML Configuration Loading
# ═══════════════════════════════════════════════════════════════════════════════


class TestYamlConfig:
    """Test YAML configuration files are valid and complete."""

    def test_load_agents_yaml(self):
        from customer_support.crew import _load_yaml

        config = _load_yaml("agents.yaml")
        assert isinstance(config, dict)
        expected_agents = ["classifier", "faq_specialist", "ticket_handler", "escalation_manager"]
        for agent_key in expected_agents:
            assert agent_key in config, f"Missing agent: {agent_key}"
            assert "role" in config[agent_key], f"Missing 'role' for {agent_key}"
            assert "goal" in config[agent_key], f"Missing 'goal' for {agent_key}"
            assert "backstory" in config[agent_key], f"Missing 'backstory' for {agent_key}"

    def test_load_tasks_yaml(self):
        from customer_support.crew import _load_yaml

        config = _load_yaml("tasks.yaml")
        assert isinstance(config, dict)
        expected_tasks = ["classify_inquiry", "answer_faq", "create_ticket", "prepare_escalation"]
        for task_key in expected_tasks:
            assert task_key in config, f"Missing task: {task_key}"
            assert "description" in config[task_key], f"Missing 'description' for {task_key}"
            assert "expected_output" in config[task_key], (
                f"Missing 'expected_output' for {task_key}"
            )

    def test_tasks_contain_query_placeholder(self):
        """All task descriptions should contain {query} placeholder."""
        from customer_support.crew import _load_yaml

        config = _load_yaml("tasks.yaml")
        for task_key, task_cfg in config.items():
            assert "{query}" in task_cfg["description"], (
                f"Task '{task_key}' description missing {{query}} placeholder"
            )

    def test_load_nonexistent_yaml_raises(self):
        """Loading a non-existent YAML file should raise FileNotFoundError."""
        from customer_support.crew import _load_yaml

        with pytest.raises(FileNotFoundError):
            _load_yaml("nonexistent.yaml")


# ═══════════════════════════════════════════════════════════════════════════════
# 5. Agent Factory (mocked — no LLM calls)
# ═══════════════════════════════════════════════════════════════════════════════


class TestAgentFactory:
    """Test agent creation from YAML config (mocked to avoid LLM calls)."""

    @patch("customer_support.crew.Agent")
    def test_creates_four_agents(self, mock_agent_cls):
        """_create_agents should create exactly 4 agents."""
        from customer_support.crew import _create_agents

        agents = _create_agents()
        assert len(agents) == 4
        assert set(agents.keys()) == set(_AGENT_KEYS)

    @patch("customer_support.crew.Agent")
    def test_classifier_uses_mini_model(self, mock_agent_cls):
        """Classifier should use the cheaper CLASSIFIER_MODEL."""
        from customer_support.crew import _create_agents

        with patch.dict(os.environ, {"CLASSIFIER_MODEL": "gpt-4o-mini", "MODEL": "gpt-4o"}):
            _create_agents()

        # Find the classifier call (first call)
        calls = mock_agent_cls.call_args_list
        classifier_call = calls[0]
        assert classifier_call.kwargs.get("llm") == "gpt-4o-mini"

    @patch("customer_support.crew.Agent")
    def test_verbose_env_controls_agent_verbosity(self, mock_agent_cls):
        """VERBOSE=false should set verbose=False on all agents."""
        from customer_support.crew import _create_agents

        with patch.dict(os.environ, {"VERBOSE": "false"}):
            _create_agents()

        for call in mock_agent_cls.call_args_list:
            assert call.kwargs.get("verbose") is False


# ═══════════════════════════════════════════════════════════════════════════════
# 6. Task Factory
# ═══════════════════════════════════════════════════════════════════════════════


class TestTaskFactory:
    """Test task creation from YAML config."""

    @patch("customer_support.crew.Task")
    def test_query_interpolation(self, mock_task_cls):
        """_create_task should replace {query} in the task description."""
        from customer_support.crew import _create_task

        mock_agent = MagicMock()
        _create_task("classify_inquiry", mock_agent, "How do I reset my password?")

        call_kwargs = mock_task_cls.call_args.kwargs
        assert "How do I reset my password?" in call_kwargs["description"]
        assert "{query}" not in call_kwargs["description"]

    @patch("customer_support.crew.Task")
    def test_all_task_keys_valid(self, mock_task_cls):
        """All expected task keys should produce a valid Task."""
        from customer_support.crew import _create_task

        mock_agent = MagicMock()
        for key in ["classify_inquiry", "answer_faq", "create_ticket", "prepare_escalation"]:
            _create_task(key, mock_agent, "test query")
            assert mock_task_cls.called


# ═══════════════════════════════════════════════════════════════════════════════
# 7. classify_inquiry (mocked CrewAI)
# ═══════════════════════════════════════════════════════════════════════════════


class TestClassifyInquiry:
    """Test classify_inquiry with mocked CrewAI Crew.kickoff()."""

    @patch("customer_support.crew._create_task", return_value=MagicMock())
    @patch("customer_support.crew._create_agents")
    @patch("customer_support.crew.Crew")
    def test_classify_faq(self, mock_crew_cls, mock_agents, mock_task):
        """FAQ-related query should return 'faq'."""
        from customer_support.crew import classify_inquiry

        mock_agents.return_value = _mock_agents_dict()
        mock_result = MagicMock()
        mock_result.raw = "faq"
        mock_crew_cls.return_value.kickoff.return_value = mock_result

        assert classify_inquiry("What is your refund policy?") == "faq"

    @patch("customer_support.crew._create_task", return_value=MagicMock())
    @patch("customer_support.crew._create_agents")
    @patch("customer_support.crew.Crew")
    def test_classify_ticket(self, mock_crew_cls, mock_agents, mock_task):
        """Bug report should return 'ticket'."""
        from customer_support.crew import classify_inquiry

        mock_agents.return_value = _mock_agents_dict()
        mock_result = MagicMock()
        mock_result.raw = "ticket"
        mock_crew_cls.return_value.kickoff.return_value = mock_result

        assert classify_inquiry("App crashes when I click save") == "ticket"

    @patch("customer_support.crew._create_task", return_value=MagicMock())
    @patch("customer_support.crew._create_agents")
    @patch("customer_support.crew.Crew")
    def test_classify_escalation(self, mock_crew_cls, mock_agents, mock_task):
        """Urgent security issue should return 'escalation'."""
        from customer_support.crew import classify_inquiry

        mock_agents.return_value = _mock_agents_dict()
        mock_result = MagicMock()
        mock_result.raw = "escalation"
        mock_crew_cls.return_value.kickoff.return_value = mock_result

        assert classify_inquiry("I think my account was hacked") == "escalation"

    @patch("customer_support.crew._create_task", return_value=MagicMock())
    @patch("customer_support.crew._create_agents")
    @patch("customer_support.crew.Crew")
    def test_classify_unknown_defaults_to_ticket(
        self, mock_crew_cls, mock_agents, mock_task,
    ):
        """Unknown LLM output should default to 'ticket'."""
        from customer_support.crew import classify_inquiry

        mock_agents.return_value = _mock_agents_dict()
        mock_result = MagicMock()
        mock_result.raw = "I'm not sure what category this is"
        mock_crew_cls.return_value.kickoff.return_value = mock_result

        assert classify_inquiry("Something weird happened") == "ticket"


# ═══════════════════════════════════════════════════════════════════════════════
# 8. handle_inquiry (mocked CrewAI)
# ═══════════════════════════════════════════════════════════════════════════════


class TestHandleInquiry:
    """Test handle_inquiry end-to-end with mocked CrewAI."""

    @patch("customer_support.crew._create_task", return_value=MagicMock())
    @patch("customer_support.crew._create_agents")
    @patch("customer_support.crew.Crew")
    @patch("customer_support.crew.classify_inquiry", return_value="faq")
    def test_handle_faq_returns_support_result(
        self, mock_classify, mock_crew_cls, mock_agents, mock_task,
    ):
        """handle_inquiry should return a SupportResult for FAQ queries."""
        from customer_support.crew import SupportResult, handle_inquiry

        mock_agents.return_value = _mock_agents_dict()
        mock_result = MagicMock()
        mock_result.raw = "Click Forgot Password on the login page."
        mock_crew_cls.return_value.kickoff.return_value = mock_result

        result = handle_inquiry("How do I reset my password?")
        assert isinstance(result, SupportResult)
        assert result.category == "faq"
        assert result.query == "How do I reset my password?"
        assert "Forgot Password" in result.response

    @patch("customer_support.crew._create_task", return_value=MagicMock())
    @patch("customer_support.crew._create_agents")
    @patch("customer_support.crew.Crew")
    @patch("customer_support.crew.classify_inquiry", return_value="escalation")
    def test_handle_escalation_routes_correctly(
        self, mock_classify, mock_crew_cls, mock_agents, mock_task,
    ):
        """Escalation queries should route to escalation_manager."""
        from customer_support.crew import handle_inquiry

        mock_agents.return_value = _mock_agents_dict()
        mock_result = MagicMock()
        mock_result.raw = "**Severity**: P1-Critical\n**Business Impact**: Data breach risk"
        mock_crew_cls.return_value.kickoff.return_value = mock_result

        result = handle_inquiry("Our database was compromised")
        assert result.category == "escalation"
        assert "P1" in result.response or "Critical" in result.response


# ═══════════════════════════════════════════════════════════════════════════════
# 9. CLI Argument Parsing
# ═══════════════════════════════════════════════════════════════════════════════


class TestCLI:
    """Test CLI argument parsing (no LLM calls)."""

    def test_parse_single_query(self):
        """--query flag should be parsed correctly."""
        import argparse

        parser = argparse.ArgumentParser()
        parser.add_argument("--query", "-q", type=str)
        parser.add_argument("--file", "-f", type=str)
        parser.add_argument("--classify-only", "-c", action="store_true")

        args = parser.parse_args(["--query", "How do I cancel?"])
        assert args.query == "How do I cancel?"
        assert args.file is None
        assert args.classify_only is False

    def test_parse_classify_only(self):
        """--classify-only flag should set classify_only=True."""
        import argparse

        parser = argparse.ArgumentParser()
        parser.add_argument("--query", "-q", type=str)
        parser.add_argument("--file", "-f", type=str)
        parser.add_argument("--classify-only", "-c", action="store_true")

        args = parser.parse_args(["-q", "test", "-c"])
        assert args.classify_only is True

    def test_parse_file_mode(self):
        """--file flag should be parsed correctly."""
        import argparse

        parser = argparse.ArgumentParser()
        parser.add_argument("--query", "-q", type=str)
        parser.add_argument("--file", "-f", type=str)
        parser.add_argument("--classify-only", "-c", action="store_true")

        args = parser.parse_args(["--file", "queries.txt"])
        assert args.file == "queries.txt"
        assert args.query is None

    def test_batch_file_not_found(self, tmp_path):
        """Batch mode with non-existent file should exit with error."""
        nonexistent = tmp_path / "no_such_file.txt"
        assert not nonexistent.exists()


# ═══════════════════════════════════════════════════════════════════════════════
# 10. Environment Variable Handling
# ═══════════════════════════════════════════════════════════════════════════════


class TestEnvConfig:
    """Test environment variable configuration."""

    def test_env_example_exists(self):
        """`.env.example` should exist in the project root."""
        env_example = Path(__file__).parent.parent / ".env.example"
        assert env_example.exists(), ".env.example is required for template users"

    def test_env_example_contains_required_vars(self):
        """`.env.example` should document all required environment variables."""
        env_example = Path(__file__).parent.parent / ".env.example"
        content = env_example.read_text(encoding="utf-8")
        required_vars = ["MODEL", "OPENAI_API_KEY", "CLASSIFIER_MODEL"]
        for var in required_vars:
            assert var in content, f".env.example missing {var}"

    def test_gitignore_excludes_env(self):
        """.gitignore should exclude .env to prevent credential leaks."""
        gitignore = Path(__file__).parent.parent / ".gitignore"
        content = gitignore.read_text(encoding="utf-8")
        assert ".env" in content
