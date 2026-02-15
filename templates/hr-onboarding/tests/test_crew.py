"""Tests for the HR onboarding assistant.

Covers:
- Onboarding guide search tool (keyword matching, edge cases)
- Employee lookup tool (valid/invalid IDs)
- Onboarding status tool (valid/invalid departments)
- Classification normalization logic
- OnboardingResult Pydantic model validation
- YAML configuration loading
- Agent factory (mocked LLM)
- Task factory
- classify_request / handle_request integration (mocked CrewAI)
- CLI argument parsing
- Environment variable handling
"""

from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

import pytest

# Helper: all agent keys for mock setup
_AGENT_KEYS = [
    "classifier", "document_collector",
    "it_setup_coordinator", "training_scheduler", "buddy_matcher",
]


def _mock_agents_dict():
    """Create a dict of MagicMock agents for all 5 roles."""
    return {k: MagicMock() for k in _AGENT_KEYS}


# ═══════════════════════════════════════════════════════════════════════════════
# 1. Onboarding Guide Search Tool
# ═══════════════════════════════════════════════════════════════════════════════


class TestOnboardingGuideSearch:
    """Test the onboarding guide search tool."""

    def test_search_finds_contract(self):
        from hr_onboarding.tools.custom_tool import search_onboarding_guide

        result = search_onboarding_guide.run("contract")
        assert "contract" in result.lower()

    def test_search_finds_tax_forms(self):
        from hr_onboarding.tools.custom_tool import search_onboarding_guide

        result = search_onboarding_guide.run("tax")
        assert "tax" in result.lower()

    def test_search_finds_laptop(self):
        from hr_onboarding.tools.custom_tool import search_onboarding_guide

        result = search_onboarding_guide.run("laptop")
        assert "laptop" in result.lower()

    def test_search_finds_orientation(self):
        from hr_onboarding.tools.custom_tool import search_onboarding_guide

        result = search_onboarding_guide.run("orientation")
        assert "orientation" in result.lower()

    def test_search_finds_buddy(self):
        from hr_onboarding.tools.custom_tool import search_onboarding_guide

        result = search_onboarding_guide.run("buddy")
        assert "buddy" in result.lower()

    def test_search_finds_vpn(self):
        from hr_onboarding.tools.custom_tool import search_onboarding_guide

        result = search_onboarding_guide.run("VPN")
        assert "vpn" in result.lower()

    def test_search_finds_compliance(self):
        from hr_onboarding.tools.custom_tool import search_onboarding_guide

        result = search_onboarding_guide.run("compliance")
        assert "compliance" in result.lower()

    def test_search_no_results(self):
        from hr_onboarding.tools.custom_tool import search_onboarding_guide

        result = search_onboarding_guide.run("xyznonexistent12345")
        assert "No onboarding guide articles found" in result

    def test_search_case_insensitive(self):
        from hr_onboarding.tools.custom_tool import search_onboarding_guide

        lower = search_onboarding_guide.run("benefits")
        upper = search_onboarding_guide.run("BENEFITS")
        assert "No onboarding guide articles found" not in lower
        assert "No onboarding guide articles found" not in upper

    def test_search_returns_truncated_results(self):
        from hr_onboarding.tools.custom_tool import search_onboarding_guide

        result = search_onboarding_guide.run("training")
        for section in result.split("---"):
            assert len(section.strip()) <= 800 or section.strip() == ""

    def test_search_empty_query(self):
        from hr_onboarding.tools.custom_tool import search_onboarding_guide

        result = search_onboarding_guide.run("")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_search_finds_badge(self):
        from hr_onboarding.tools.custom_tool import search_onboarding_guide

        result = search_onboarding_guide.run("badge")
        assert "No onboarding guide articles found" not in result

    def test_search_finds_payroll(self):
        from hr_onboarding.tools.custom_tool import search_onboarding_guide

        result = search_onboarding_guide.run("payroll")
        assert "No onboarding guide articles found" not in result


# ═══════════════════════════════════════════════════════════════════════════════
# 2. Employee Lookup Tool
# ═══════════════════════════════════════════════════════════════════════════════


class TestEmployeeLookup:
    """Test the employee lookup tool."""

    def test_lookup_preboarding_employee(self):
        from hr_onboarding.tools.custom_tool import lookup_employee

        result = lookup_employee.run("EMP-001")
        assert "Alice Johnson" in result
        assert "Engineering" in result
        assert "pre-boarding" in result

    def test_lookup_in_progress_employee(self):
        from hr_onboarding.tools.custom_tool import lookup_employee

        result = lookup_employee.run("EMP-002")
        assert "Carlos Rivera" in result
        assert "Marketing" in result
        assert "in_progress" in result

    def test_lookup_finance_employee(self):
        from hr_onboarding.tools.custom_tool import lookup_employee

        result = lookup_employee.run("EMP-003")
        assert "Fatima Al-Hassan" in result
        assert "Finance" in result

    def test_lookup_completed_employee(self):
        from hr_onboarding.tools.custom_tool import lookup_employee

        result = lookup_employee.run("EMP-004")
        assert "Kenji Yamamoto" in result
        assert "completed" in result
        assert "Sales" in result

    def test_lookup_hr_employee(self):
        from hr_onboarding.tools.custom_tool import lookup_employee

        result = lookup_employee.run("EMP-005")
        assert "Priya Nair" in result
        assert "Human Resources" in result

    def test_lookup_shows_document_status(self):
        from hr_onboarding.tools.custom_tool import lookup_employee

        result = lookup_employee.run("EMP-001")
        assert "contract" in result.lower()
        assert "tax_forms" in result

    def test_lookup_shows_it_setup_status(self):
        from hr_onboarding.tools.custom_tool import lookup_employee

        result = lookup_employee.run("EMP-002")
        assert "laptop" in result
        assert "email" in result

    def test_lookup_shows_training_status(self):
        from hr_onboarding.tools.custom_tool import lookup_employee

        result = lookup_employee.run("EMP-004")
        assert "orientation" in result
        assert "compliance" in result

    def test_lookup_invalid_employee(self):
        from hr_onboarding.tools.custom_tool import lookup_employee

        result = lookup_employee.run("EMP-999")
        assert "Employee not found" in result

    def test_lookup_case_insensitive(self):
        from hr_onboarding.tools.custom_tool import lookup_employee

        result = lookup_employee.run("emp-001")
        assert "Alice Johnson" in result

    def test_lookup_empty_id(self):
        from hr_onboarding.tools.custom_tool import lookup_employee

        result = lookup_employee.run("")
        assert "Employee not found" in result


# ═══════════════════════════════════════════════════════════════════════════════
# 3. Onboarding Status Tool
# ═══════════════════════════════════════════════════════════════════════════════


class TestOnboardingStatus:
    """Test the onboarding status check tool."""

    def test_engineering_status(self):
        from hr_onboarding.tools.custom_tool import check_onboarding_status

        result = check_onboarding_status.run("engineering")
        assert "Engineering" in result
        assert "Pre-boarding" in result

    def test_marketing_status(self):
        from hr_onboarding.tools.custom_tool import check_onboarding_status

        result = check_onboarding_status.run("marketing")
        assert "Marketing" in result
        assert "No overdue items" in result

    def test_sales_status_with_overdue(self):
        from hr_onboarding.tools.custom_tool import check_onboarding_status

        result = check_onboarding_status.run("sales")
        assert "Sales" in result
        assert "Overdue" in result
        assert "compliance training" in result.lower()

    def test_finance_status(self):
        from hr_onboarding.tools.custom_tool import check_onboarding_status

        result = check_onboarding_status.run("finance")
        assert "Finance" in result

    def test_hr_status(self):
        from hr_onboarding.tools.custom_tool import check_onboarding_status

        result = check_onboarding_status.run("human resources")
        assert "Human Resources" in result

    def test_all_departments(self):
        from hr_onboarding.tools.custom_tool import check_onboarding_status

        result = check_onboarding_status.run("all")
        assert "Company-Wide" in result
        assert "Pre-boarding" in result
        assert "Completed" in result

    def test_all_shows_overdue_items(self):
        from hr_onboarding.tools.custom_tool import check_onboarding_status

        result = check_onboarding_status.run("all")
        assert "Overdue" in result

    def test_unknown_department(self):
        from hr_onboarding.tools.custom_tool import check_onboarding_status

        result = check_onboarding_status.run("nonexistent_department")
        assert "Department not found" in result
        assert "Available" in result

    def test_department_case_insensitive(self):
        from hr_onboarding.tools.custom_tool import check_onboarding_status

        result = check_onboarding_status.run("Engineering")
        assert "Engineering" in result
        assert "Pre-boarding" in result


# ═══════════════════════════════════════════════════════════════════════════════
# 4. Classification Normalization Logic
# ═══════════════════════════════════════════════════════════════════════════════


class TestClassificationNormalization:
    """Test request classification normalization logic.

    This tests the raw-output-to-category mapping logic used in
    _normalize_category() without calling any LLM.
    """

    @pytest.mark.parametrize(
        "raw_output, expected",
        [
            # Direct category matches
            ("document_collection", "document_collection"),
            ("DOCUMENT_COLLECTION", "document_collection"),
            ("it_setup", "it_setup"),
            ("IT_SETUP", "it_setup"),
            ("training_schedule", "training_schedule"),
            ("TRAINING_SCHEDULE", "training_schedule"),
            ("buddy_match", "buddy_match"),
            ("BUDDY_MATCH", "buddy_match"),
            # Fallback keyword matches — documents
            ("I need to submit my contract", "document_collection"),
            ("where do I fill out tax forms", "document_collection"),
            ("w-4 form help", "document_collection"),
            ("i-9 verification question", "document_collection"),
            ("bank details for payroll", "document_collection"),
            ("benefits enrollment deadline", "document_collection"),
            ("emergency contact update", "document_collection"),
            # Fallback keyword matches — IT setup
            ("I need a laptop", "it_setup"),
            ("when will I get my email account", "it_setup"),
            ("vpn access not working", "it_setup"),
            ("badge for the office", "it_setup"),
            ("software installation needed", "it_setup"),
            ("permission to access the network drive", "it_setup"),
            ("it setup for my computer", "it_setup"),
            # Fallback keyword matches — training
            ("when is orientation", "training_schedule"),
            ("compliance training required", "training_schedule"),
            ("any available course for me", "training_schedule"),
            ("e-learning modules to complete", "training_schedule"),
            ("schedule my training sessions", "training_schedule"),
            ("class for new hires", "training_schedule"),
            ("workshop on data analysis", "training_schedule"),
            ("my onboarding plan", "training_schedule"),
            # Fallback keyword matches — buddy
            ("assign me a buddy", "buddy_match"),
            ("need a mentor", "buddy_match"),
            ("team introduction", "buddy_match"),
            ("welcome lunch", "buddy_match"),
            ("meet my team", "buddy_match"),
            ("social events for new hires", "buddy_match"),
            # Default fallback
            ("unknown request type", "document_collection"),
            ("", "document_collection"),
            ("   ", "document_collection"),
        ],
    )
    def test_normalize(self, raw_output: str, expected: str):
        """Category normalization should match expected output."""
        from hr_onboarding.crew import _normalize_category

        result = _normalize_category(raw_output.strip().lower())
        assert result == expected, f"Failed for input: {raw_output!r}"


# ═══════════════════════════════════════════════════════════════════════════════
# 5. OnboardingResult Pydantic Model
# ═══════════════════════════════════════════════════════════════════════════════


class TestOnboardingResult:
    """Test the OnboardingResult model."""

    def test_valid_document_collection_result(self):
        from hr_onboarding.crew import OnboardingResult

        r = OnboardingResult(
            query="What documents do I need?",
            category="document_collection",
            response="Here are the required documents...",
        )
        assert r.query == "What documents do I need?"
        assert r.category == "document_collection"

    def test_valid_it_setup_result(self):
        from hr_onboarding.crew import OnboardingResult

        r = OnboardingResult(
            query="When do I get my laptop?",
            category="it_setup",
            response="Your laptop will be ready...",
        )
        assert r.category == "it_setup"

    def test_valid_training_schedule_result(self):
        from hr_onboarding.crew import OnboardingResult

        r = OnboardingResult(
            query="When is orientation?",
            category="training_schedule",
            response="Orientation is scheduled...",
        )
        assert r.category == "training_schedule"

    def test_valid_buddy_match_result(self):
        from hr_onboarding.crew import OnboardingResult

        r = OnboardingResult(
            query="Who is my buddy?",
            category="buddy_match",
            response="Your buddy is...",
        )
        assert r.category == "buddy_match"

    def test_invalid_category_raises(self):
        from hr_onboarding.crew import OnboardingResult

        with pytest.raises(Exception):
            OnboardingResult(
                query="test",
                category="invalid_category",
                response="test",
            )

    def test_empty_response_allowed(self):
        from hr_onboarding.crew import OnboardingResult

        r = OnboardingResult(
            query="test", category="document_collection", response=""
        )
        assert r.response == ""

    def test_long_query_allowed(self):
        from hr_onboarding.crew import OnboardingResult

        long_query = "x" * 10000
        r = OnboardingResult(
            query=long_query, category="it_setup", response="ok"
        )
        assert len(r.query) == 10000


# ═══════════════════════════════════════════════════════════════════════════════
# 6. YAML Configuration Loading
# ═══════════════════════════════════════════════════════════════════════════════


class TestYAMLConfig:
    """Test YAML configuration file loading."""

    def test_agents_yaml_loads(self):
        from hr_onboarding.crew import _load_yaml

        config = _load_yaml("agents.yaml")
        assert "classifier" in config
        assert "document_collector" in config
        assert "it_setup_coordinator" in config
        assert "training_scheduler" in config
        assert "buddy_matcher" in config

    def test_tasks_yaml_loads(self):
        from hr_onboarding.crew import _load_yaml

        config = _load_yaml("tasks.yaml")
        assert "classify_request" in config
        assert "collect_documents" in config
        assert "coordinate_it_setup" in config
        assert "schedule_training" in config
        assert "match_buddy" in config

    def test_agents_have_required_fields(self):
        from hr_onboarding.crew import _load_yaml

        config = _load_yaml("agents.yaml")
        for agent_key in config:
            agent = config[agent_key]
            assert "role" in agent, f"{agent_key} missing role"
            assert "goal" in agent, f"{agent_key} missing goal"
            assert "backstory" in agent, f"{agent_key} missing backstory"

    def test_tasks_have_required_fields(self):
        from hr_onboarding.crew import _load_yaml

        config = _load_yaml("tasks.yaml")
        for task_key in config:
            task = config[task_key]
            assert "description" in task, f"{task_key} missing description"
            assert "expected_output" in task, (
                f"{task_key} missing expected_output"
            )


# ═══════════════════════════════════════════════════════════════════════════════
# 7. Agent Factory
# ═══════════════════════════════════════════════════════════════════════════════


class TestAgentFactory:
    """Test agent creation from YAML configuration."""

    @patch("hr_onboarding.crew.Agent")
    def test_creates_all_agents(self, mock_agent_cls):
        from hr_onboarding.crew import _create_agents

        mock_agent_cls.return_value = MagicMock()
        agents = _create_agents()
        assert set(agents.keys()) == set(_AGENT_KEYS)

    @patch("hr_onboarding.crew.Agent")
    def test_classifier_uses_classifier_model(self, mock_agent_cls):
        from hr_onboarding.crew import _create_agents

        mock_agent_cls.return_value = MagicMock()
        with patch.dict(os.environ, {"CLASSIFIER_MODEL": "gpt-4o-mini"}):
            _create_agents()

        calls = mock_agent_cls.call_args_list
        classifier_call = calls[0]
        assert classifier_call.kwargs["llm"] == "gpt-4o-mini"

    @patch("hr_onboarding.crew.Agent")
    def test_specialists_use_main_model(self, mock_agent_cls):
        from hr_onboarding.crew import _create_agents

        mock_agent_cls.return_value = MagicMock()
        with patch.dict(os.environ, {"MODEL": "gpt-4o"}):
            _create_agents()

        calls = mock_agent_cls.call_args_list
        for call in calls[1:]:
            assert call.kwargs["llm"] == "gpt-4o"


# ═══════════════════════════════════════════════════════════════════════════════
# 8. Task Factory
# ═══════════════════════════════════════════════════════════════════════════════


class TestTaskFactory:
    """Test task creation from YAML configuration."""

    @patch("hr_onboarding.crew.Task")
    def test_create_task_interpolates_query(self, mock_task_cls):
        from hr_onboarding.crew import _create_task

        mock_task_cls.return_value = MagicMock()
        agent = MagicMock()
        _create_task("classify_request", agent, "need my tax forms")

        call_kwargs = mock_task_cls.call_args.kwargs
        assert "need my tax forms" in call_kwargs["description"]

    @patch("hr_onboarding.crew.Task")
    def test_create_task_sets_agent(self, mock_task_cls):
        from hr_onboarding.crew import _create_task

        mock_task_cls.return_value = MagicMock()
        agent = MagicMock()
        _create_task("collect_documents", agent, "test")

        call_kwargs = mock_task_cls.call_args.kwargs
        assert call_kwargs["agent"] is agent


# ═══════════════════════════════════════════════════════════════════════════════
# 9. classify_request (mocked)
# ═══════════════════════════════════════════════════════════════════════════════


class TestClassifyRequest:
    """Test classify_request with mocked CrewAI."""

    @patch("hr_onboarding.crew._create_agents")
    @patch("hr_onboarding.crew.Crew")
    @patch("hr_onboarding.crew._create_task")
    def test_classify_document(self, mock_task, mock_crew_cls, mock_agents):
        from hr_onboarding.crew import classify_request

        mock_agents.return_value = _mock_agents_dict()
        mock_result = MagicMock()
        mock_result.raw = "document_collection"
        mock_crew_cls.return_value.kickoff.return_value = mock_result

        assert classify_request("I need to submit my W-4 form") == "document_collection"

    @patch("hr_onboarding.crew._create_agents")
    @patch("hr_onboarding.crew.Crew")
    @patch("hr_onboarding.crew._create_task")
    def test_classify_it_setup(self, mock_task, mock_crew_cls, mock_agents):
        from hr_onboarding.crew import classify_request

        mock_agents.return_value = _mock_agents_dict()
        mock_result = MagicMock()
        mock_result.raw = "it_setup"
        mock_crew_cls.return_value.kickoff.return_value = mock_result

        assert classify_request("When do I get my laptop?") == "it_setup"

    @patch("hr_onboarding.crew._create_agents")
    @patch("hr_onboarding.crew.Crew")
    @patch("hr_onboarding.crew._create_task")
    def test_classify_training(self, mock_task, mock_crew_cls, mock_agents):
        from hr_onboarding.crew import classify_request

        mock_agents.return_value = _mock_agents_dict()
        mock_result = MagicMock()
        mock_result.raw = "training_schedule"
        mock_crew_cls.return_value.kickoff.return_value = mock_result

        assert classify_request("When is my orientation?") == "training_schedule"

    @patch("hr_onboarding.crew._create_agents")
    @patch("hr_onboarding.crew.Crew")
    @patch("hr_onboarding.crew._create_task")
    def test_classify_buddy(self, mock_task, mock_crew_cls, mock_agents):
        from hr_onboarding.crew import classify_request

        mock_agents.return_value = _mock_agents_dict()
        mock_result = MagicMock()
        mock_result.raw = "buddy_match"
        mock_crew_cls.return_value.kickoff.return_value = mock_result

        assert classify_request("Can I get a mentor?") == "buddy_match"

    @patch("hr_onboarding.crew._create_agents")
    @patch("hr_onboarding.crew.Crew")
    @patch("hr_onboarding.crew._create_task")
    def test_classify_fallback(self, mock_task, mock_crew_cls, mock_agents):
        from hr_onboarding.crew import classify_request

        mock_agents.return_value = _mock_agents_dict()
        mock_result = MagicMock()
        mock_result.raw = "something random"
        mock_crew_cls.return_value.kickoff.return_value = mock_result

        assert classify_request("blah blah") == "document_collection"


# ═══════════════════════════════════════════════════════════════════════════════
# 10. handle_request (mocked)
# ═══════════════════════════════════════════════════════════════════════════════


class TestHandleRequest:
    """Test handle_request with mocked CrewAI."""

    @patch("hr_onboarding.crew._create_agents")
    @patch("hr_onboarding.crew.Crew")
    @patch("hr_onboarding.crew._create_task")
    @patch("hr_onboarding.crew.classify_request")
    def test_handle_document_request(
        self, mock_classify, mock_task, mock_crew_cls, mock_agents
    ):
        from hr_onboarding.crew import handle_request

        mock_classify.return_value = "document_collection"
        mock_agents.return_value = _mock_agents_dict()
        mock_result = MagicMock()
        mock_result.raw = "Here are the required documents..."
        mock_crew_cls.return_value.kickoff.return_value = mock_result

        result = handle_request("What documents do I need?")
        assert result.category == "document_collection"
        assert "documents" in result.response.lower()

    @patch("hr_onboarding.crew._create_agents")
    @patch("hr_onboarding.crew.Crew")
    @patch("hr_onboarding.crew._create_task")
    @patch("hr_onboarding.crew.classify_request")
    def test_handle_it_setup_request(
        self, mock_classify, mock_task, mock_crew_cls, mock_agents
    ):
        from hr_onboarding.crew import handle_request

        mock_classify.return_value = "it_setup"
        mock_agents.return_value = _mock_agents_dict()
        mock_result = MagicMock()
        mock_result.raw = "Your laptop will be ready on day one..."
        mock_crew_cls.return_value.kickoff.return_value = mock_result

        result = handle_request("When do I get my laptop?")
        assert result.category == "it_setup"

    @patch("hr_onboarding.crew._create_agents")
    @patch("hr_onboarding.crew.Crew")
    @patch("hr_onboarding.crew._create_task")
    @patch("hr_onboarding.crew.classify_request")
    def test_handle_preserves_query(
        self, mock_classify, mock_task, mock_crew_cls, mock_agents
    ):
        from hr_onboarding.crew import handle_request

        mock_classify.return_value = "training_schedule"
        mock_agents.return_value = _mock_agents_dict()
        mock_result = MagicMock()
        mock_result.raw = "Orientation is on your first day..."
        mock_crew_cls.return_value.kickoff.return_value = mock_result

        result = handle_request("When is orientation?")
        assert result.query == "When is orientation?"

    @patch("hr_onboarding.crew._create_agents")
    @patch("hr_onboarding.crew.Crew")
    @patch("hr_onboarding.crew._create_task")
    @patch("hr_onboarding.crew.classify_request")
    def test_handle_buddy_request(
        self, mock_classify, mock_task, mock_crew_cls, mock_agents
    ):
        from hr_onboarding.crew import handle_request

        mock_classify.return_value = "buddy_match"
        mock_agents.return_value = _mock_agents_dict()
        mock_result = MagicMock()
        mock_result.raw = "Your buddy has been assigned..."
        mock_crew_cls.return_value.kickoff.return_value = mock_result

        result = handle_request("Can you assign me a buddy?")
        assert result.category == "buddy_match"


# ═══════════════════════════════════════════════════════════════════════════════
# 11. CLI Argument Parsing
# ═══════════════════════════════════════════════════════════════════════════════


class TestCLIArgs:
    """Test CLI argument parsing."""

    def test_parse_query_arg(self):
        import argparse

        parser = argparse.ArgumentParser()
        parser.add_argument("--query", "-q", type=str)
        parser.add_argument("--file", "-f", type=str)
        parser.add_argument("--classify-only", "-c", action="store_true")

        args = parser.parse_args(["--query", "submit my tax forms"])
        assert args.query == "submit my tax forms"
        assert not args.classify_only

    def test_parse_classify_only(self):
        import argparse

        parser = argparse.ArgumentParser()
        parser.add_argument("--query", "-q", type=str)
        parser.add_argument("--file", "-f", type=str)
        parser.add_argument("--classify-only", "-c", action="store_true")

        args = parser.parse_args(["-q", "test", "-c"])
        assert args.classify_only

    def test_parse_file_arg(self):
        import argparse

        parser = argparse.ArgumentParser()
        parser.add_argument("--query", "-q", type=str)
        parser.add_argument("--file", "-f", type=str)
        parser.add_argument("--classify-only", "-c", action="store_true")

        args = parser.parse_args(["--file", "requests.txt"])
        assert args.file == "requests.txt"

    def test_parse_no_args(self):
        import argparse

        parser = argparse.ArgumentParser()
        parser.add_argument("--query", "-q", type=str)
        parser.add_argument("--file", "-f", type=str)
        parser.add_argument("--classify-only", "-c", action="store_true")

        args = parser.parse_args([])
        assert args.query is None
        assert args.file is None
        assert not args.classify_only


# ═══════════════════════════════════════════════════════════════════════════════
# 12. Environment Variable Handling
# ═══════════════════════════════════════════════════════════════════════════════


class TestEnvironmentVars:
    """Test environment variable handling."""

    @patch("hr_onboarding.crew.Agent")
    def test_default_model(self, mock_agent_cls):
        from hr_onboarding.crew import _create_agents

        mock_agent_cls.return_value = MagicMock()
        env = {k: v for k, v in os.environ.items() if k != "MODEL"}
        with patch.dict(os.environ, env, clear=True):
            _create_agents()

        for call in mock_agent_cls.call_args_list[1:]:
            assert call.kwargs["llm"] == "gpt-4o"

    @patch("hr_onboarding.crew.Agent")
    def test_custom_model(self, mock_agent_cls):
        from hr_onboarding.crew import _create_agents

        mock_agent_cls.return_value = MagicMock()
        with patch.dict(os.environ, {"MODEL": "anthropic/claude-sonnet-4-20250514"}):
            _create_agents()

        for call in mock_agent_cls.call_args_list[1:]:
            assert call.kwargs["llm"] == "anthropic/claude-sonnet-4-20250514"

    @patch("hr_onboarding.crew.Agent")
    def test_verbose_default_true(self, mock_agent_cls):
        from hr_onboarding.crew import _create_agents

        mock_agent_cls.return_value = MagicMock()
        env = {k: v for k, v in os.environ.items() if k != "VERBOSE"}
        with patch.dict(os.environ, env, clear=True):
            _create_agents()

        for call in mock_agent_cls.call_args_list:
            assert call.kwargs["verbose"] is True
