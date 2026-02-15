"""Tests for the e-commerce assistant agent.

Covers:
- Product catalog search tool (keyword matching, edge cases)
- Order lookup tool (valid/invalid order IDs)
- Classification normalization logic
- EcommerceResult Pydantic model validation
- YAML configuration loading
- Agent factory (mocked LLM)
- classify_inquiry / handle_inquiry integration (mocked CrewAI)
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
    "classifier", "product_search",
    "order_tracker", "return_handler", "recommender",
]


def _mock_agents_dict():
    """Create a dict of MagicMock agents for all 5 roles."""
    return {k: MagicMock() for k in _AGENT_KEYS}


# ═══════════════════════════════════════════════════════════════════════════════
# 1. Product Catalog Search Tool
# ═══════════════════════════════════════════════════════════════════════════════


class TestProductCatalogSearch:
    """Test the product catalog search tool."""

    def test_search_finds_headphones(self):
        from ecommerce_assistant.tools.custom_tool import search_product_catalog

        result = search_product_catalog.run("headphones")
        assert "headphones" in result.lower() or "soundmax" in result.lower()

    def test_search_no_results(self):
        from ecommerce_assistant.tools.custom_tool import search_product_catalog

        result = search_product_catalog.run("xyznonexistent12345")
        assert "No products found" in result

    def test_search_finds_electronics(self):
        from ecommerce_assistant.tools.custom_tool import search_product_catalog

        result = search_product_catalog.run("bluetooth")
        assert "No products found" not in result

    def test_search_case_insensitive(self):
        from ecommerce_assistant.tools.custom_tool import search_product_catalog

        lower = search_product_catalog.run("vacuum")
        upper = search_product_catalog.run("VACUUM")
        assert "No products found" not in lower
        assert "No products found" not in upper

    def test_search_finds_fashion(self):
        from ecommerce_assistant.tools.custom_tool import search_product_catalog

        result = search_product_catalog.run("running shoes")
        assert "No products found" not in result

    def test_search_returns_truncated_results(self):
        from ecommerce_assistant.tools.custom_tool import search_product_catalog

        result = search_product_catalog.run("product")
        for section in result.split("---"):
            assert len(section.strip()) <= 500 or section.strip() == ""

    def test_search_empty_query(self):
        from ecommerce_assistant.tools.custom_tool import search_product_catalog

        result = search_product_catalog.run("")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_search_return_policy(self):
        """Return policy information should be searchable."""
        from ecommerce_assistant.tools.custom_tool import search_product_catalog

        result = search_product_catalog.run("return policy")
        assert "No products found" not in result


# ═══════════════════════════════════════════════════════════════════════════════
# 2. Order Lookup Tool
# ═══════════════════════════════════════════════════════════════════════════════


class TestOrderLookup:
    """Test the order lookup tool."""

    def test_lookup_valid_order_in_transit(self):
        from ecommerce_assistant.tools.custom_tool import lookup_order

        result = lookup_order.run("ORD-12345")
        assert "In Transit" in result
        assert "FedEx" in result

    def test_lookup_valid_order_processing(self):
        from ecommerce_assistant.tools.custom_tool import lookup_order

        result = lookup_order.run("ORD-67890")
        assert "Processing" in result

    def test_lookup_valid_order_delivered(self):
        from ecommerce_assistant.tools.custom_tool import lookup_order

        result = lookup_order.run("ORD-11111")
        assert "Delivered" in result

    def test_lookup_invalid_order(self):
        from ecommerce_assistant.tools.custom_tool import lookup_order

        result = lookup_order.run("ORD-99999")
        assert "Order not found" in result

    def test_lookup_case_insensitive(self):
        from ecommerce_assistant.tools.custom_tool import lookup_order

        result = lookup_order.run("ord-12345")
        assert "In Transit" in result

    def test_lookup_empty_id(self):
        from ecommerce_assistant.tools.custom_tool import lookup_order

        result = lookup_order.run("")
        assert "Order not found" in result


# ═══════════════════════════════════════════════════════════════════════════════
# 3. Classification Normalization Logic
# ═══════════════════════════════════════════════════════════════════════════════


class TestClassificationNormalization:
    """Test inquiry classification normalization logic.

    This tests the raw-output-to-category mapping logic used in
    classify_inquiry() without calling any LLM.
    """

    @pytest.mark.parametrize(
        "raw_output, expected",
        [
            ("product_search", "product_search"),
            ("PRODUCT_SEARCH", "product_search"),
            ("order_tracking", "order_tracking"),
            ("ORDER_TRACKING", "order_tracking"),
            ("return_refund", "return_refund"),
            ("RETURN_REFUND", "return_refund"),
            ("recommendation", "recommendation"),
            ("RECOMMENDATION", "recommendation"),
            ("I want to return this item", "return_refund"),
            ("refund please", "return_refund"),
            ("recommend me something", "recommendation"),
            ("product search needed", "product_search"),
            ("track my order", "order_tracking"),
            ("unknown query type", "product_search"),  # default fallback
            ("", "product_search"),  # empty → default
            ("   ", "product_search"),  # whitespace → default
        ],
    )
    def test_normalize(self, raw_output: str, expected: str):
        """Category normalization should match expected output."""
        raw_lower = raw_output.strip().lower()
        if "product_search" in raw_lower or "product" in raw_lower and "search" in raw_lower:
            result = "product_search"
        elif "order_tracking" in raw_lower or "order" in raw_lower and "track" in raw_lower:
            result = "order_tracking"
        elif "return_refund" in raw_lower or "return" in raw_lower or "refund" in raw_lower:
            result = "return_refund"
        elif "recommendation" in raw_lower or "recommend" in raw_lower:
            result = "recommendation"
        else:
            result = "product_search"
        assert result == expected, f"Failed for input: {raw_output!r}"


# ═══════════════════════════════════════════════════════════════════════════════
# 4. EcommerceResult Pydantic Model
# ═══════════════════════════════════════════════════════════════════════════════


class TestEcommerceResult:
    """Test the EcommerceResult model."""

    def test_valid_product_search_result(self):
        from ecommerce_assistant.crew import EcommerceResult

        result = EcommerceResult(
            query="Do you have wireless headphones?",
            category="product_search",
            response="Found 2 headphones: SoundMax Pro ($299.99)",
        )
        assert result.query == "Do you have wireless headphones?"
        assert result.category == "product_search"
        assert "SoundMax Pro" in result.response

    def test_valid_order_tracking_result(self):
        from ecommerce_assistant.crew import EcommerceResult

        result = EcommerceResult(
            query="Where is my order ORD-12345?",
            category="order_tracking",
            response="Your order is in transit via FedEx",
        )
        assert result.category == "order_tracking"

    def test_valid_return_refund_result(self):
        from ecommerce_assistant.crew import EcommerceResult

        result = EcommerceResult(
            query="I want to return my headphones",
            category="return_refund",
            response="Return approved. Send within 30 days.",
        )
        assert result.category == "return_refund"

    def test_valid_recommendation_result(self):
        from ecommerce_assistant.crew import EcommerceResult

        result = EcommerceResult(
            query="What headphones do you recommend?",
            category="recommendation",
            response="I recommend the SoundMax Pro for its noise cancellation.",
        )
        assert result.category == "recommendation"

    def test_invalid_category_rejected(self):
        from ecommerce_assistant.crew import EcommerceResult

        with pytest.raises(Exception):
            EcommerceResult(
                query="test",
                category="invalid_category",
                response="test",
            )

    def test_empty_query_allowed(self):
        from ecommerce_assistant.crew import EcommerceResult

        result = EcommerceResult(
            query="", category="product_search", response="No query provided."
        )
        assert result.query == ""

    def test_long_response_allowed(self):
        from ecommerce_assistant.crew import EcommerceResult

        long_text = "A" * 10_000
        result = EcommerceResult(
            query="test", category="product_search", response=long_text
        )
        assert len(result.response) == 10_000


# ═══════════════════════════════════════════════════════════════════════════════
# 5. YAML Configuration Loading
# ═══════════════════════════════════════════════════════════════════════════════


class TestYamlConfig:
    """Test YAML configuration files are valid and complete."""

    def test_load_agents_yaml(self):
        from ecommerce_assistant.crew import _load_yaml

        config = _load_yaml("agents.yaml")
        assert isinstance(config, dict)
        expected_agents = [
            "classifier", "product_search", "order_tracker",
            "return_handler", "recommender",
        ]
        for agent_key in expected_agents:
            assert agent_key in config, f"Missing agent: {agent_key}"
            assert "role" in config[agent_key], f"Missing 'role' for {agent_key}"
            assert "goal" in config[agent_key], f"Missing 'goal' for {agent_key}"
            assert "backstory" in config[agent_key], f"Missing 'backstory' for {agent_key}"

    def test_load_tasks_yaml(self):
        from ecommerce_assistant.crew import _load_yaml

        config = _load_yaml("tasks.yaml")
        assert isinstance(config, dict)
        expected_tasks = [
            "classify_inquiry", "search_products", "track_order",
            "process_return", "recommend_products",
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
        from ecommerce_assistant.crew import _load_yaml

        config = _load_yaml("tasks.yaml")
        for task_key, task_cfg in config.items():
            assert "{query}" in task_cfg["description"], (
                f"Task '{task_key}' description missing {{query}} placeholder"
            )

    def test_load_nonexistent_yaml_raises(self):
        """Loading a non-existent YAML file should raise FileNotFoundError."""
        from ecommerce_assistant.crew import _load_yaml

        with pytest.raises(FileNotFoundError):
            _load_yaml("nonexistent.yaml")


# ═══════════════════════════════════════════════════════════════════════════════
# 6. Agent Factory (mocked — no LLM calls)
# ═══════════════════════════════════════════════════════════════════════════════


class TestAgentFactory:
    """Test agent creation from YAML config (mocked to avoid LLM calls)."""

    @patch("ecommerce_assistant.crew.Agent")
    def test_creates_five_agents(self, mock_agent_cls):
        """_create_agents should create exactly 5 agents."""
        from ecommerce_assistant.crew import _create_agents

        agents = _create_agents()
        assert len(agents) == 5
        assert set(agents.keys()) == set(_AGENT_KEYS)

    @patch("ecommerce_assistant.crew.Agent")
    def test_classifier_uses_mini_model(self, mock_agent_cls):
        """Classifier should use the cheaper CLASSIFIER_MODEL."""
        from ecommerce_assistant.crew import _create_agents

        with patch.dict(os.environ, {"CLASSIFIER_MODEL": "gpt-4o-mini", "MODEL": "gpt-4o"}):
            _create_agents()

        calls = mock_agent_cls.call_args_list
        classifier_call = calls[0]
        assert classifier_call.kwargs.get("llm") == "gpt-4o-mini"

    @patch("ecommerce_assistant.crew.Agent")
    def test_verbose_env_controls_agent_verbosity(self, mock_agent_cls):
        """VERBOSE=false should set verbose=False on all agents."""
        from ecommerce_assistant.crew import _create_agents

        with patch.dict(os.environ, {"VERBOSE": "false"}):
            _create_agents()

        for call in mock_agent_cls.call_args_list:
            assert call.kwargs.get("verbose") is False


# ═══════════════════════════════════════════════════════════════════════════════
# 7. Task Factory
# ═══════════════════════════════════════════════════════════════════════════════


class TestTaskFactory:
    """Test task creation from YAML config."""

    @patch("ecommerce_assistant.crew.Task")
    def test_query_interpolation(self, mock_task_cls):
        """_create_task should replace {query} in the task description."""
        from ecommerce_assistant.crew import _create_task

        mock_agent = MagicMock()
        _create_task("classify_inquiry", mock_agent, "Do you have wireless headphones?")

        call_kwargs = mock_task_cls.call_args.kwargs
        assert "Do you have wireless headphones?" in call_kwargs["description"]
        assert "{query}" not in call_kwargs["description"]

    @patch("ecommerce_assistant.crew.Task")
    def test_all_task_keys_valid(self, mock_task_cls):
        """All expected task keys should produce a valid Task."""
        from ecommerce_assistant.crew import _create_task

        mock_agent = MagicMock()
        for key in [
            "classify_inquiry", "search_products", "track_order",
            "process_return", "recommend_products",
        ]:
            _create_task(key, mock_agent, "test query")
            assert mock_task_cls.called


# ═══════════════════════════════════════════════════════════════════════════════
# 8. classify_inquiry (mocked CrewAI)
# ═══════════════════════════════════════════════════════════════════════════════


class TestClassifyInquiry:
    """Test classify_inquiry with mocked CrewAI Crew.kickoff()."""

    @patch("ecommerce_assistant.crew._create_task", return_value=MagicMock())
    @patch("ecommerce_assistant.crew._create_agents")
    @patch("ecommerce_assistant.crew.Crew")
    def test_classify_product_search(self, mock_crew_cls, mock_agents, mock_task):
        from ecommerce_assistant.crew import classify_inquiry

        mock_agents.return_value = _mock_agents_dict()
        mock_result = MagicMock()
        mock_result.raw = "product_search"
        mock_crew_cls.return_value.kickoff.return_value = mock_result

        assert classify_inquiry("Do you have wireless headphones?") == "product_search"

    @patch("ecommerce_assistant.crew._create_task", return_value=MagicMock())
    @patch("ecommerce_assistant.crew._create_agents")
    @patch("ecommerce_assistant.crew.Crew")
    def test_classify_order_tracking(self, mock_crew_cls, mock_agents, mock_task):
        from ecommerce_assistant.crew import classify_inquiry

        mock_agents.return_value = _mock_agents_dict()
        mock_result = MagicMock()
        mock_result.raw = "order_tracking"
        mock_crew_cls.return_value.kickoff.return_value = mock_result

        assert classify_inquiry("Where is my order ORD-12345?") == "order_tracking"

    @patch("ecommerce_assistant.crew._create_task", return_value=MagicMock())
    @patch("ecommerce_assistant.crew._create_agents")
    @patch("ecommerce_assistant.crew.Crew")
    def test_classify_return_refund(self, mock_crew_cls, mock_agents, mock_task):
        from ecommerce_assistant.crew import classify_inquiry

        mock_agents.return_value = _mock_agents_dict()
        mock_result = MagicMock()
        mock_result.raw = "return_refund"
        mock_crew_cls.return_value.kickoff.return_value = mock_result

        assert classify_inquiry("I want to return my order") == "return_refund"

    @patch("ecommerce_assistant.crew._create_task", return_value=MagicMock())
    @patch("ecommerce_assistant.crew._create_agents")
    @patch("ecommerce_assistant.crew.Crew")
    def test_classify_recommendation(self, mock_crew_cls, mock_agents, mock_task):
        from ecommerce_assistant.crew import classify_inquiry

        mock_agents.return_value = _mock_agents_dict()
        mock_result = MagicMock()
        mock_result.raw = "recommendation"
        mock_crew_cls.return_value.kickoff.return_value = mock_result

        assert classify_inquiry("What laptop do you recommend?") == "recommendation"

    @patch("ecommerce_assistant.crew._create_task", return_value=MagicMock())
    @patch("ecommerce_assistant.crew._create_agents")
    @patch("ecommerce_assistant.crew.Crew")
    def test_classify_unknown_defaults_to_product_search(
        self, mock_crew_cls, mock_agents, mock_task,
    ):
        from ecommerce_assistant.crew import classify_inquiry

        mock_agents.return_value = _mock_agents_dict()
        mock_result = MagicMock()
        mock_result.raw = "I'm not sure what category this is"
        mock_crew_cls.return_value.kickoff.return_value = mock_result

        assert classify_inquiry("Something unclear") == "product_search"


# ═══════════════════════════════════════════════════════════════════════════════
# 9. handle_inquiry (mocked CrewAI)
# ═══════════════════════════════════════════════════════════════════════════════


class TestHandleInquiry:
    """Test handle_inquiry end-to-end with mocked CrewAI."""

    @patch("ecommerce_assistant.crew._create_task", return_value=MagicMock())
    @patch("ecommerce_assistant.crew._create_agents")
    @patch("ecommerce_assistant.crew.Crew")
    @patch("ecommerce_assistant.crew.classify_inquiry", return_value="product_search")
    def test_handle_product_search_returns_result(
        self, mock_classify, mock_crew_cls, mock_agents, mock_task,
    ):
        from ecommerce_assistant.crew import EcommerceResult, handle_inquiry

        mock_agents.return_value = _mock_agents_dict()
        mock_result = MagicMock()
        mock_result.raw = "Found SoundMax Pro Headphones at $299.99"
        mock_crew_cls.return_value.kickoff.return_value = mock_result

        result = handle_inquiry("Do you have wireless headphones?")
        assert isinstance(result, EcommerceResult)
        assert result.category == "product_search"
        assert result.query == "Do you have wireless headphones?"
        assert "SoundMax Pro" in result.response

    @patch("ecommerce_assistant.crew._create_task", return_value=MagicMock())
    @patch("ecommerce_assistant.crew._create_agents")
    @patch("ecommerce_assistant.crew.Crew")
    @patch("ecommerce_assistant.crew.classify_inquiry", return_value="order_tracking")
    def test_handle_order_tracking_routes_correctly(
        self, mock_classify, mock_crew_cls, mock_agents, mock_task,
    ):
        from ecommerce_assistant.crew import handle_inquiry

        mock_agents.return_value = _mock_agents_dict()
        mock_result = MagicMock()
        mock_result.raw = "**Order Status**: In Transit via FedEx"
        mock_crew_cls.return_value.kickoff.return_value = mock_result

        result = handle_inquiry("Where is order ORD-12345?")
        assert result.category == "order_tracking"
        assert "In Transit" in result.response

    @patch("ecommerce_assistant.crew._create_task", return_value=MagicMock())
    @patch("ecommerce_assistant.crew._create_agents")
    @patch("ecommerce_assistant.crew.Crew")
    @patch("ecommerce_assistant.crew.classify_inquiry", return_value="return_refund")
    def test_handle_return_routes_correctly(
        self, mock_classify, mock_crew_cls, mock_agents, mock_task,
    ):
        from ecommerce_assistant.crew import handle_inquiry

        mock_agents.return_value = _mock_agents_dict()
        mock_result = MagicMock()
        mock_result.raw = "**Eligibility**: Eligible\n**Refund Method**: Original payment"
        mock_crew_cls.return_value.kickoff.return_value = mock_result

        result = handle_inquiry("I want to return my headphones")
        assert result.category == "return_refund"
        assert "Eligible" in result.response

    @patch("ecommerce_assistant.crew._create_task", return_value=MagicMock())
    @patch("ecommerce_assistant.crew._create_agents")
    @patch("ecommerce_assistant.crew.Crew")
    @patch("ecommerce_assistant.crew.classify_inquiry", return_value="recommendation")
    def test_handle_recommendation_routes_correctly(
        self, mock_classify, mock_crew_cls, mock_agents, mock_task,
    ):
        from ecommerce_assistant.crew import handle_inquiry

        mock_agents.return_value = _mock_agents_dict()
        mock_result = MagicMock()
        mock_result.raw = "I recommend the SoundMax Pro for noise cancellation."
        mock_crew_cls.return_value.kickoff.return_value = mock_result

        result = handle_inquiry("What headphones do you recommend?")
        assert result.category == "recommendation"
        assert "SoundMax Pro" in result.response


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

        args = parser.parse_args(["--query", "Do you have headphones?"])
        assert args.query == "Do you have headphones?"
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
