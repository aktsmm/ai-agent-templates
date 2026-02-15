"""Tests for the IT helpdesk agent.

Covers:
- Knowledge base search tool (keyword matching, edge cases)
- Ticket lookup tool (valid/invalid IDs)
- System status tool (valid/invalid services)
- Classification normalization logic
- HelpdeskResult Pydantic model validation
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
    "classifier", "password_reset",
    "software_troubleshooter", "network_support", "hardware_support",
]


def _mock_agents_dict():
    """Create a dict of MagicMock agents for all 5 roles."""
    return {k: MagicMock() for k in _AGENT_KEYS}


# ═══════════════════════════════════════════════════════════════════════════════
# 1. Knowledge Base Search Tool
# ═══════════════════════════════════════════════════════════════════════════════


class TestKnowledgeBaseSearch:
    """Test the knowledge base search tool."""

    def test_search_finds_password(self):
        from it_helpdesk.tools.custom_tool import search_knowledge_base

        result = search_knowledge_base.run("password")
        assert "password" in result.lower()

    def test_search_finds_vpn(self):
        from it_helpdesk.tools.custom_tool import search_knowledge_base

        result = search_knowledge_base.run("VPN")
        assert "vpn" in result.lower()

    def test_search_finds_printer(self):
        from it_helpdesk.tools.custom_tool import search_knowledge_base

        result = search_knowledge_base.run("printer")
        assert "printer" in result.lower()

    def test_search_finds_laptop(self):
        from it_helpdesk.tools.custom_tool import search_knowledge_base

        result = search_knowledge_base.run("laptop")
        assert "laptop" in result.lower()

    def test_search_no_results(self):
        from it_helpdesk.tools.custom_tool import search_knowledge_base

        result = search_knowledge_base.run("xyznonexistent12345")
        assert "No knowledge base articles found" in result

    def test_search_case_insensitive(self):
        from it_helpdesk.tools.custom_tool import search_knowledge_base

        lower = search_knowledge_base.run("wi-fi")
        upper = search_knowledge_base.run("WI-FI")
        assert "No knowledge base articles found" not in lower
        assert "No knowledge base articles found" not in upper

    def test_search_returns_truncated_results(self):
        from it_helpdesk.tools.custom_tool import search_knowledge_base

        result = search_knowledge_base.run("password")
        for section in result.split("---"):
            assert len(section.strip()) <= 800 or section.strip() == ""

    def test_search_empty_query(self):
        from it_helpdesk.tools.custom_tool import search_knowledge_base

        result = search_knowledge_base.run("")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_search_finds_mfa(self):
        from it_helpdesk.tools.custom_tool import search_knowledge_base

        result = search_knowledge_base.run("MFA")
        assert "No knowledge base articles found" not in result

    def test_search_finds_teams(self):
        from it_helpdesk.tools.custom_tool import search_knowledge_base

        result = search_knowledge_base.run("Teams")
        assert "No knowledge base articles found" not in result

    def test_search_finds_blue_screen(self):
        from it_helpdesk.tools.custom_tool import search_knowledge_base

        result = search_knowledge_base.run("Blue Screen")
        assert "No knowledge base articles found" not in result


# ═══════════════════════════════════════════════════════════════════════════════
# 2. Ticket Lookup Tool
# ═══════════════════════════════════════════════════════════════════════════════


class TestTicketLookup:
    """Test the ticket lookup tool."""

    def test_lookup_valid_ticket_in_progress(self):
        from it_helpdesk.tools.custom_tool import lookup_ticket

        result = lookup_ticket.run("TKT-001")
        assert "In Progress" in result
        assert "IAM Team" in result

    def test_lookup_valid_ticket_open(self):
        from it_helpdesk.tools.custom_tool import lookup_ticket

        result = lookup_ticket.run("TKT-002")
        assert "Open" in result
        assert "Teams" in result

    def test_lookup_valid_ticket_resolved(self):
        from it_helpdesk.tools.custom_tool import lookup_ticket

        result = lookup_ticket.run("TKT-003")
        assert "Resolved" in result

    def test_lookup_valid_ticket_waiting(self):
        from it_helpdesk.tools.custom_tool import lookup_ticket

        result = lookup_ticket.run("TKT-004")
        assert "Waiting for Parts" in result

    def test_lookup_valid_ticket_escalated(self):
        from it_helpdesk.tools.custom_tool import lookup_ticket

        result = lookup_ticket.run("TKT-005")
        assert "Escalated" in result
        assert "Critical" in result

    def test_lookup_invalid_ticket(self):
        from it_helpdesk.tools.custom_tool import lookup_ticket

        result = lookup_ticket.run("TKT-999")
        assert "Ticket not found" in result

    def test_lookup_case_insensitive(self):
        from it_helpdesk.tools.custom_tool import lookup_ticket

        result = lookup_ticket.run("tkt-001")
        assert "In Progress" in result

    def test_lookup_empty_id(self):
        from it_helpdesk.tools.custom_tool import lookup_ticket

        result = lookup_ticket.run("")
        assert "Ticket not found" in result


# ═══════════════════════════════════════════════════════════════════════════════
# 3. System Status Tool
# ═══════════════════════════════════════════════════════════════════════════════


class TestSystemStatus:
    """Test the system status check tool."""

    def test_vpn_status(self):
        from it_helpdesk.tools.custom_tool import check_system_status

        result = check_system_status.run("vpn")
        assert "Operational" in result
        assert "GlobalProtect" in result

    def test_email_status(self):
        from it_helpdesk.tools.custom_tool import check_system_status

        result = check_system_status.run("email")
        assert "Operational" in result

    def test_teams_degraded(self):
        from it_helpdesk.tools.custom_tool import check_system_status

        result = check_system_status.run("teams")
        assert "Degraded" in result

    def test_wifi_partial_outage(self):
        from it_helpdesk.tools.custom_tool import check_system_status

        result = check_system_status.run("wifi")
        assert "Partial Outage" in result

    def test_erp_status(self):
        from it_helpdesk.tools.custom_tool import check_system_status

        result = check_system_status.run("erp")
        assert "Operational" in result

    def test_printing_status(self):
        from it_helpdesk.tools.custom_tool import check_system_status

        result = check_system_status.run("printing")
        assert "Operational" in result

    def test_active_directory_status(self):
        from it_helpdesk.tools.custom_tool import check_system_status

        result = check_system_status.run("active_directory")
        assert "Operational" in result

    def test_unknown_service(self):
        from it_helpdesk.tools.custom_tool import check_system_status

        result = check_system_status.run("nonexistent_service")
        assert "not found" in result.lower()
        assert "Available services" in result

    def test_service_with_spaces(self):
        from it_helpdesk.tools.custom_tool import check_system_status

        result = check_system_status.run("active directory")
        assert "Operational" in result


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
            ("password_reset", "password_reset"),
            ("PASSWORD_RESET", "password_reset"),
            ("software_issue", "software_issue"),
            ("SOFTWARE_ISSUE", "software_issue"),
            ("network_issue", "network_issue"),
            ("NETWORK_ISSUE", "network_issue"),
            ("hardware_issue", "hardware_issue"),
            ("HARDWARE_ISSUE", "hardware_issue"),
            # Fallback keyword matches — password
            ("I forgot my password", "password_reset"),
            ("account lockout", "password_reset"),
            ("my account is locked", "password_reset"),
            ("need to reset MFA", "password_reset"),
            ("can't login to my computer", "password_reset"),
            # Fallback keyword matches — software
            ("software not working", "software_issue"),
            ("install Adobe", "software_issue"),
            ("Teams keeps crashing", "software_issue"),
            ("need to update Office", "software_issue"),
            ("app won't open", "software_issue"),
            # Fallback keyword matches — network
            ("vpn won't connect", "network_issue"),
            ("wifi is down", "network_issue"),
            ("can't connect to internet", "network_issue"),
            ("dns not resolving", "network_issue"),
            ("network connectivity problem", "network_issue"),
            ("wi-fi keeps dropping", "network_issue"),
            # Fallback keyword matches — hardware
            ("laptop won't turn on", "hardware_issue"),
            ("printer not working", "hardware_issue"),
            ("monitor flickering", "hardware_issue"),
            ("keyboard is broken", "hardware_issue"),
            ("need a new mouse", "hardware_issue"),
            # Default fallback
            ("unknown request type", "software_issue"),
            ("", "software_issue"),
            ("   ", "software_issue"),
        ],
    )
    def test_normalize(self, raw_output: str, expected: str):
        """Category normalization should match expected output."""
        from it_helpdesk.crew import _normalize_category

        result = _normalize_category(raw_output.strip().lower())
        assert result == expected, f"Failed for input: {raw_output!r}"


# ═══════════════════════════════════════════════════════════════════════════════
# 5. HelpdeskResult Pydantic Model
# ═══════════════════════════════════════════════════════════════════════════════


class TestHelpdeskResult:
    """Test the HelpdeskResult model."""

    def test_valid_password_reset_result(self):
        from it_helpdesk.crew import HelpdeskResult

        r = HelpdeskResult(
            query="Reset my password",
            category="password_reset",
            response="Follow these steps...",
        )
        assert r.query == "Reset my password"
        assert r.category == "password_reset"

    def test_valid_software_issue_result(self):
        from it_helpdesk.crew import HelpdeskResult

        r = HelpdeskResult(
            query="Teams crashes",
            category="software_issue",
            response="Try clearing cache...",
        )
        assert r.category == "software_issue"

    def test_valid_network_issue_result(self):
        from it_helpdesk.crew import HelpdeskResult

        r = HelpdeskResult(
            query="VPN disconnects",
            category="network_issue",
            response="Check your connection...",
        )
        assert r.category == "network_issue"

    def test_valid_hardware_issue_result(self):
        from it_helpdesk.crew import HelpdeskResult

        r = HelpdeskResult(
            query="Printer jammed",
            category="hardware_issue",
            response="Open the front panel...",
        )
        assert r.category == "hardware_issue"

    def test_invalid_category_raises(self):
        from it_helpdesk.crew import HelpdeskResult

        with pytest.raises(Exception):
            HelpdeskResult(
                query="test",
                category="invalid_category",
                response="test",
            )

    def test_empty_response_allowed(self):
        from it_helpdesk.crew import HelpdeskResult

        r = HelpdeskResult(
            query="test", category="password_reset", response=""
        )
        assert r.response == ""

    def test_long_query_allowed(self):
        from it_helpdesk.crew import HelpdeskResult

        long_query = "x" * 10000
        r = HelpdeskResult(
            query=long_query, category="software_issue", response="ok"
        )
        assert len(r.query) == 10000


# ═══════════════════════════════════════════════════════════════════════════════
# 6. YAML Configuration Loading
# ═══════════════════════════════════════════════════════════════════════════════


class TestYAMLConfig:
    """Test YAML configuration file loading."""

    def test_agents_yaml_loads(self):
        from it_helpdesk.crew import _load_yaml

        config = _load_yaml("agents.yaml")
        assert "classifier" in config
        assert "password_reset" in config
        assert "software_troubleshooter" in config
        assert "network_support" in config
        assert "hardware_support" in config

    def test_tasks_yaml_loads(self):
        from it_helpdesk.crew import _load_yaml

        config = _load_yaml("tasks.yaml")
        assert "classify_request" in config
        assert "reset_password" in config
        assert "troubleshoot_software" in config
        assert "diagnose_network" in config
        assert "handle_hardware" in config

    def test_agents_have_required_fields(self):
        from it_helpdesk.crew import _load_yaml

        config = _load_yaml("agents.yaml")
        for agent_key in config:
            agent = config[agent_key]
            assert "role" in agent, f"{agent_key} missing role"
            assert "goal" in agent, f"{agent_key} missing goal"
            assert "backstory" in agent, f"{agent_key} missing backstory"

    def test_tasks_have_required_fields(self):
        from it_helpdesk.crew import _load_yaml

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

    @patch("it_helpdesk.crew.Agent")
    def test_creates_all_agents(self, mock_agent_cls):
        from it_helpdesk.crew import _create_agents

        mock_agent_cls.return_value = MagicMock()
        agents = _create_agents()
        assert set(agents.keys()) == set(_AGENT_KEYS)

    @patch("it_helpdesk.crew.Agent")
    def test_classifier_uses_classifier_model(self, mock_agent_cls):
        from it_helpdesk.crew import _create_agents

        mock_agent_cls.return_value = MagicMock()
        with patch.dict(os.environ, {"CLASSIFIER_MODEL": "gpt-4o-mini"}):
            _create_agents()

        # Find the classifier call (first call)
        calls = mock_agent_cls.call_args_list
        classifier_call = calls[0]
        assert classifier_call.kwargs["llm"] == "gpt-4o-mini"

    @patch("it_helpdesk.crew.Agent")
    def test_specialists_use_main_model(self, mock_agent_cls):
        from it_helpdesk.crew import _create_agents

        mock_agent_cls.return_value = MagicMock()
        with patch.dict(os.environ, {"MODEL": "gpt-4o"}):
            _create_agents()

        calls = mock_agent_cls.call_args_list
        # All calls after the first (classifier) should use gpt-4o
        for call in calls[1:]:
            assert call.kwargs["llm"] == "gpt-4o"


# ═══════════════════════════════════════════════════════════════════════════════
# 8. Task Factory
# ═══════════════════════════════════════════════════════════════════════════════


class TestTaskFactory:
    """Test task creation from YAML configuration."""

    @patch("it_helpdesk.crew.Task")
    def test_create_task_interpolates_query(self, mock_task_cls):
        from it_helpdesk.crew import _create_task

        mock_task_cls.return_value = MagicMock()
        agent = MagicMock()
        _create_task("classify_request", agent, "reset my password")

        call_kwargs = mock_task_cls.call_args.kwargs
        assert "reset my password" in call_kwargs["description"]

    @patch("it_helpdesk.crew.Task")
    def test_create_task_sets_agent(self, mock_task_cls):
        from it_helpdesk.crew import _create_task

        mock_task_cls.return_value = MagicMock()
        agent = MagicMock()
        _create_task("reset_password", agent, "test")

        call_kwargs = mock_task_cls.call_args.kwargs
        assert call_kwargs["agent"] is agent


# ═══════════════════════════════════════════════════════════════════════════════
# 9. classify_request (mocked)
# ═══════════════════════════════════════════════════════════════════════════════


class TestClassifyRequest:
    """Test classify_request with mocked CrewAI."""

    @patch("it_helpdesk.crew._create_agents")
    @patch("it_helpdesk.crew.Crew")
    @patch("it_helpdesk.crew._create_task")
    def test_classify_password(self, mock_task, mock_crew_cls, mock_agents):
        from it_helpdesk.crew import classify_request

        mock_agents.return_value = _mock_agents_dict()
        mock_result = MagicMock()
        mock_result.raw = "password_reset"
        mock_crew_cls.return_value.kickoff.return_value = mock_result

        assert classify_request("I forgot my password") == "password_reset"

    @patch("it_helpdesk.crew._create_agents")
    @patch("it_helpdesk.crew.Crew")
    @patch("it_helpdesk.crew._create_task")
    def test_classify_software(self, mock_task, mock_crew_cls, mock_agents):
        from it_helpdesk.crew import classify_request

        mock_agents.return_value = _mock_agents_dict()
        mock_result = MagicMock()
        mock_result.raw = "software_issue"
        mock_crew_cls.return_value.kickoff.return_value = mock_result

        assert classify_request("Excel keeps crashing") == "software_issue"

    @patch("it_helpdesk.crew._create_agents")
    @patch("it_helpdesk.crew.Crew")
    @patch("it_helpdesk.crew._create_task")
    def test_classify_network(self, mock_task, mock_crew_cls, mock_agents):
        from it_helpdesk.crew import classify_request

        mock_agents.return_value = _mock_agents_dict()
        mock_result = MagicMock()
        mock_result.raw = "network_issue"
        mock_crew_cls.return_value.kickoff.return_value = mock_result

        assert classify_request("VPN not connecting") == "network_issue"

    @patch("it_helpdesk.crew._create_agents")
    @patch("it_helpdesk.crew.Crew")
    @patch("it_helpdesk.crew._create_task")
    def test_classify_hardware(self, mock_task, mock_crew_cls, mock_agents):
        from it_helpdesk.crew import classify_request

        mock_agents.return_value = _mock_agents_dict()
        mock_result = MagicMock()
        mock_result.raw = "hardware_issue"
        mock_crew_cls.return_value.kickoff.return_value = mock_result

        assert classify_request("Laptop screen cracked") == "hardware_issue"

    @patch("it_helpdesk.crew._create_agents")
    @patch("it_helpdesk.crew.Crew")
    @patch("it_helpdesk.crew._create_task")
    def test_classify_fallback(self, mock_task, mock_crew_cls, mock_agents):
        from it_helpdesk.crew import classify_request

        mock_agents.return_value = _mock_agents_dict()
        mock_result = MagicMock()
        mock_result.raw = "something random"
        mock_crew_cls.return_value.kickoff.return_value = mock_result

        assert classify_request("blah blah") == "software_issue"


# ═══════════════════════════════════════════════════════════════════════════════
# 10. handle_request (mocked)
# ═══════════════════════════════════════════════════════════════════════════════


class TestHandleRequest:
    """Test handle_request with mocked CrewAI."""

    @patch("it_helpdesk.crew._create_agents")
    @patch("it_helpdesk.crew.Crew")
    @patch("it_helpdesk.crew._create_task")
    @patch("it_helpdesk.crew.classify_request")
    def test_handle_password_request(
        self, mock_classify, mock_task, mock_crew_cls, mock_agents
    ):
        from it_helpdesk.crew import handle_request

        mock_classify.return_value = "password_reset"
        mock_agents.return_value = _mock_agents_dict()
        mock_result = MagicMock()
        mock_result.raw = "Here are the steps to reset your password..."
        mock_crew_cls.return_value.kickoff.return_value = mock_result

        result = handle_request("Reset my password please")
        assert result.category == "password_reset"
        assert "reset" in result.response.lower()

    @patch("it_helpdesk.crew._create_agents")
    @patch("it_helpdesk.crew.Crew")
    @patch("it_helpdesk.crew._create_task")
    @patch("it_helpdesk.crew.classify_request")
    def test_handle_network_request(
        self, mock_classify, mock_task, mock_crew_cls, mock_agents
    ):
        from it_helpdesk.crew import handle_request

        mock_classify.return_value = "network_issue"
        mock_agents.return_value = _mock_agents_dict()
        mock_result = MagicMock()
        mock_result.raw = "Check your VPN settings..."
        mock_crew_cls.return_value.kickoff.return_value = mock_result

        result = handle_request("VPN keeps disconnecting")
        assert result.category == "network_issue"

    @patch("it_helpdesk.crew._create_agents")
    @patch("it_helpdesk.crew.Crew")
    @patch("it_helpdesk.crew._create_task")
    @patch("it_helpdesk.crew.classify_request")
    def test_handle_preserves_query(
        self, mock_classify, mock_task, mock_crew_cls, mock_agents
    ):
        from it_helpdesk.crew import handle_request

        mock_classify.return_value = "software_issue"
        mock_agents.return_value = _mock_agents_dict()
        mock_result = MagicMock()
        mock_result.raw = "Try reinstalling..."
        mock_crew_cls.return_value.kickoff.return_value = mock_result

        result = handle_request("Teams won't start")
        assert result.query == "Teams won't start"

    @patch("it_helpdesk.crew._create_agents")
    @patch("it_helpdesk.crew.Crew")
    @patch("it_helpdesk.crew._create_task")
    @patch("it_helpdesk.crew.classify_request")
    def test_handle_hardware_request(
        self, mock_classify, mock_task, mock_crew_cls, mock_agents
    ):
        from it_helpdesk.crew import handle_request

        mock_classify.return_value = "hardware_issue"
        mock_agents.return_value = _mock_agents_dict()
        mock_result = MagicMock()
        mock_result.raw = "Submit a repair ticket..."
        mock_crew_cls.return_value.kickoff.return_value = mock_result

        result = handle_request("My laptop keyboard is broken")
        assert result.category == "hardware_issue"


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

        args = parser.parse_args(["--query", "reset password"])
        assert args.query == "reset password"
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

    @patch("it_helpdesk.crew.Agent")
    def test_default_model(self, mock_agent_cls):
        from it_helpdesk.crew import _create_agents

        mock_agent_cls.return_value = MagicMock()
        env = {k: v for k, v in os.environ.items() if k != "MODEL"}
        with patch.dict(os.environ, env, clear=True):
            _create_agents()

        # Specialist calls should use default gpt-4o
        for call in mock_agent_cls.call_args_list[1:]:
            assert call.kwargs["llm"] == "gpt-4o"

    @patch("it_helpdesk.crew.Agent")
    def test_custom_model(self, mock_agent_cls):
        from it_helpdesk.crew import _create_agents

        mock_agent_cls.return_value = MagicMock()
        with patch.dict(os.environ, {"MODEL": "anthropic/claude-sonnet-4-20250514"}):
            _create_agents()

        for call in mock_agent_cls.call_args_list[1:]:
            assert call.kwargs["llm"] == "anthropic/claude-sonnet-4-20250514"

    @patch("it_helpdesk.crew.Agent")
    def test_verbose_default_true(self, mock_agent_cls):
        from it_helpdesk.crew import _create_agents

        mock_agent_cls.return_value = MagicMock()
        env = {k: v for k, v in os.environ.items() if k != "VERBOSE"}
        with patch.dict(os.environ, env, clear=True):
            _create_agents()

        for call in mock_agent_cls.call_args_list:
            assert call.kwargs["verbose"] is True
