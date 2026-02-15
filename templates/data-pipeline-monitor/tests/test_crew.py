"""Tests for the data pipeline monitor agent.

Covers:
- Pipeline status tool (valid/invalid IDs)
- Data metrics tool (valid/invalid datasets)
- Runbook search tool (keyword matching, edge cases)
- Classification normalization logic
- DataPipelineResult Pydantic model validation
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
    "classifier", "pipeline_health_checker",
    "data_quality_analyzer", "alert_manager", "recovery_advisor",
]


def _mock_agents_dict():
    """Create a dict of MagicMock agents for all 5 roles."""
    return {k: MagicMock() for k in _AGENT_KEYS}


# ═══════════════════════════════════════════════════════════════════════════════
# 1. Pipeline Status Tool
# ═══════════════════════════════════════════════════════════════════════════════


class TestPipelineStatus:
    """Test the pipeline status check tool."""

    def test_etl001_running(self):
        from data_pipeline_monitor.tools.custom_tool import check_pipeline_status

        result = check_pipeline_status.run("ETL-001")
        assert "running" in result.lower()
        assert "Customer Data Sync" in result

    def test_etl002_completed(self):
        from data_pipeline_monitor.tools.custom_tool import check_pipeline_status

        result = check_pipeline_status.run("ETL-002")
        assert "completed" in result.lower()
        assert "SAP" in result

    def test_etl003_failed(self):
        from data_pipeline_monitor.tools.custom_tool import check_pipeline_status

        result = check_pipeline_status.run("ETL-003")
        assert "failed" in result.lower()
        assert "ConnectionError" in result

    def test_etl004_delayed(self):
        from data_pipeline_monitor.tools.custom_tool import check_pipeline_status

        result = check_pipeline_status.run("ETL-004")
        assert "delayed" in result.lower()
        assert "Upstream dependency" in result

    def test_etl005_scheduled(self):
        from data_pipeline_monitor.tools.custom_tool import check_pipeline_status

        result = check_pipeline_status.run("ETL-005")
        assert "scheduled" in result.lower()
        assert "Workday" in result

    def test_invalid_pipeline(self):
        from data_pipeline_monitor.tools.custom_tool import check_pipeline_status

        result = check_pipeline_status.run("ETL-999")
        assert "Pipeline not found" in result
        assert "Available pipelines" in result

    def test_case_insensitive(self):
        from data_pipeline_monitor.tools.custom_tool import check_pipeline_status

        result = check_pipeline_status.run("etl-001")
        assert "running" in result.lower()

    def test_empty_id(self):
        from data_pipeline_monitor.tools.custom_tool import check_pipeline_status

        result = check_pipeline_status.run("")
        assert "Pipeline not found" in result


# ═══════════════════════════════════════════════════════════════════════════════
# 2. Data Metrics Tool
# ═══════════════════════════════════════════════════════════════════════════════


class TestDataMetrics:
    """Test the data metrics query tool."""

    def test_customers_metrics(self):
        from data_pipeline_monitor.tools.custom_tool import query_data_metrics

        result = query_data_metrics.run("customers")
        assert "dim_customers" in result
        assert "99.2" in result

    def test_products_schema_drift(self):
        from data_pipeline_monitor.tools.custom_tool import query_data_metrics

        result = query_data_metrics.run("products")
        assert "True" in result
        assert "sustainability_score" in result

    def test_transactions_metrics(self):
        from data_pipeline_monitor.tools.custom_tool import query_data_metrics

        result = query_data_metrics.run("transactions")
        assert "fact_transactions" in result
        assert "15000000" in result

    def test_marketing_events_low_completeness(self):
        from data_pipeline_monitor.tools.custom_tool import query_data_metrics

        result = query_data_metrics.run("marketing_events")
        assert "85.3" in result
        assert "14.7" in result

    def test_payroll_metrics(self):
        from data_pipeline_monitor.tools.custom_tool import query_data_metrics

        result = query_data_metrics.run("payroll")
        assert "fact_payroll" in result
        assert "100.0" in result

    def test_invalid_dataset(self):
        from data_pipeline_monitor.tools.custom_tool import query_data_metrics

        result = query_data_metrics.run("nonexistent")
        assert "Dataset not found" in result
        assert "Available datasets" in result

    def test_case_insensitive(self):
        from data_pipeline_monitor.tools.custom_tool import query_data_metrics

        result = query_data_metrics.run("Customers")
        assert "dim_customers" in result

    def test_with_spaces(self):
        from data_pipeline_monitor.tools.custom_tool import query_data_metrics

        result = query_data_metrics.run("marketing events")
        assert "fact_marketing_events" in result


# ═══════════════════════════════════════════════════════════════════════════════
# 3. Runbook Search Tool
# ═══════════════════════════════════════════════════════════════════════════════


class TestRunbookSearch:
    """Test the runbook search tool."""

    def test_search_finds_connection(self):
        from data_pipeline_monitor.tools.custom_tool import search_runbook

        result = search_runbook.run("Connection Errors")
        assert "connection" in result.lower()

    def test_search_finds_timeout(self):
        from data_pipeline_monitor.tools.custom_tool import search_runbook

        result = search_runbook.run("Timeout")
        assert "timeout" in result.lower()

    def test_search_finds_retry(self):
        from data_pipeline_monitor.tools.custom_tool import search_runbook

        result = search_runbook.run("Retry")
        assert "retry" in result.lower()

    def test_search_finds_rollback(self):
        from data_pipeline_monitor.tools.custom_tool import search_runbook

        result = search_runbook.run("Rollback")
        assert "rollback" in result.lower()

    def test_search_finds_escalation(self):
        from data_pipeline_monitor.tools.custom_tool import search_runbook

        result = search_runbook.run("Escalation")
        assert "escalat" in result.lower()

    def test_search_no_results(self):
        from data_pipeline_monitor.tools.custom_tool import search_runbook

        result = search_runbook.run("xyznonexistent12345")
        assert "No runbook articles found" in result

    def test_search_case_insensitive(self):
        from data_pipeline_monitor.tools.custom_tool import search_runbook

        lower = search_runbook.run("schema")
        upper = search_runbook.run("SCHEMA")
        assert "No runbook articles found" not in lower
        assert "No runbook articles found" not in upper

    def test_search_returns_truncated_results(self):
        from data_pipeline_monitor.tools.custom_tool import search_runbook

        result = search_runbook.run("pipeline")
        for section in result.split("---"):
            assert len(section.strip()) <= 800 or section.strip() == ""

    def test_search_empty_query(self):
        from data_pipeline_monitor.tools.custom_tool import search_runbook

        result = search_runbook.run("")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_search_finds_backfill(self):
        from data_pipeline_monitor.tools.custom_tool import search_runbook

        result = search_runbook.run("Backfill")
        assert "No runbook articles found" not in result

    def test_search_finds_severity(self):
        from data_pipeline_monitor.tools.custom_tool import search_runbook

        result = search_runbook.run("Severity")
        assert "No runbook articles found" not in result


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
            ("pipeline_health", "pipeline_health"),
            ("PIPELINE_HEALTH", "pipeline_health"),
            ("data_quality", "data_quality"),
            ("DATA_QUALITY", "data_quality"),
            ("alert_management", "alert_management"),
            ("ALERT_MANAGEMENT", "alert_management"),
            ("recovery", "recovery"),
            ("RECOVERY", "recovery"),
            # Fallback keyword matches — pipeline health
            ("check the pipeline status", "pipeline_health"),
            ("ETL job is slow", "pipeline_health"),
            ("pipeline execution failed", "pipeline_health"),
            ("show me the run status", "pipeline_health"),
            ("throughput is low", "pipeline_health"),
            ("check the schedule", "pipeline_health"),
            ("airflow dag issue", "pipeline_health"),
            # Fallback keyword matches — data quality
            ("data quality is poor", "data_quality"),
            ("completeness is below threshold", "data_quality"),
            ("freshness SLA missed", "data_quality"),
            ("schema drift detected", "data_quality"),
            ("too many null values", "data_quality"),
            ("duplicate records found", "data_quality"),
            ("anomaly in the data", "data_quality"),
            # Fallback keyword matches — alert management
            ("set up an alert for failures", "alert_management"),
            ("configure notification channel", "alert_management"),
            ("escalation policy needed", "alert_management"),
            ("pagerduty integration", "alert_management"),
            ("incident response process", "alert_management"),
            ("SLA breach notification", "alert_management"),
            ("on-call rotation", "alert_management"),
            # Fallback keyword matches — recovery
            ("how to recover from this failure", "recovery"),
            ("retry after the timeout", "recovery"),
            ("rollback the last deployment", "recovery"),
            ("backfill missing data", "recovery"),
            ("restart the failed worker", "recovery"),
            ("fix the connection error", "recovery"),
            ("restore from backup", "recovery"),
            ("failover to secondary", "recovery"),
            # Default fallback
            ("unknown request type", "pipeline_health"),
            ("", "pipeline_health"),
            ("   ", "pipeline_health"),
        ],
    )
    def test_normalize(self, raw_output: str, expected: str):
        """Category normalization should match expected output."""
        from data_pipeline_monitor.crew import _normalize_category

        result = _normalize_category(raw_output.strip().lower())
        assert result == expected, f"Failed for input: {raw_output!r}"


# ═══════════════════════════════════════════════════════════════════════════════
# 5. DataPipelineResult Pydantic Model
# ═══════════════════════════════════════════════════════════════════════════════


class TestDataPipelineResult:
    """Test the DataPipelineResult model."""

    def test_valid_pipeline_health_result(self):
        from data_pipeline_monitor.crew import DataPipelineResult

        r = DataPipelineResult(
            query="Check ETL-001 status",
            category="pipeline_health",
            response="Pipeline is running normally...",
        )
        assert r.query == "Check ETL-001 status"
        assert r.category == "pipeline_health"

    def test_valid_data_quality_result(self):
        from data_pipeline_monitor.crew import DataPipelineResult

        r = DataPipelineResult(
            query="Check customers data quality",
            category="data_quality",
            response="Completeness is at 99.2%...",
        )
        assert r.category == "data_quality"

    def test_valid_alert_management_result(self):
        from data_pipeline_monitor.crew import DataPipelineResult

        r = DataPipelineResult(
            query="Set up PagerDuty alerts",
            category="alert_management",
            response="Configure the integration...",
        )
        assert r.category == "alert_management"

    def test_valid_recovery_result(self):
        from data_pipeline_monitor.crew import DataPipelineResult

        r = DataPipelineResult(
            query="Recover failed pipeline",
            category="recovery",
            response="Retry with exponential backoff...",
        )
        assert r.category == "recovery"

    def test_invalid_category_raises(self):
        from data_pipeline_monitor.crew import DataPipelineResult

        with pytest.raises(Exception):
            DataPipelineResult(
                query="test",
                category="invalid_category",
                response="test",
            )

    def test_empty_response_allowed(self):
        from data_pipeline_monitor.crew import DataPipelineResult

        r = DataPipelineResult(
            query="test", category="pipeline_health", response=""
        )
        assert r.response == ""

    def test_long_query_allowed(self):
        from data_pipeline_monitor.crew import DataPipelineResult

        long_query = "x" * 10000
        r = DataPipelineResult(
            query=long_query, category="data_quality", response="ok"
        )
        assert len(r.query) == 10000


# ═══════════════════════════════════════════════════════════════════════════════
# 6. YAML Configuration Loading
# ═══════════════════════════════════════════════════════════════════════════════


class TestYAMLConfig:
    """Test YAML configuration file loading."""

    def test_agents_yaml_loads(self):
        from data_pipeline_monitor.crew import _load_yaml

        config = _load_yaml("agents.yaml")
        assert "classifier" in config
        assert "pipeline_health_checker" in config
        assert "data_quality_analyzer" in config
        assert "alert_manager" in config
        assert "recovery_advisor" in config

    def test_tasks_yaml_loads(self):
        from data_pipeline_monitor.crew import _load_yaml

        config = _load_yaml("tasks.yaml")
        assert "classify_request" in config
        assert "check_pipeline" in config
        assert "analyze_data_quality" in config
        assert "manage_alerts" in config
        assert "advise_recovery" in config

    def test_agents_have_required_fields(self):
        from data_pipeline_monitor.crew import _load_yaml

        config = _load_yaml("agents.yaml")
        for agent_key in config:
            agent = config[agent_key]
            assert "role" in agent, f"{agent_key} missing role"
            assert "goal" in agent, f"{agent_key} missing goal"
            assert "backstory" in agent, f"{agent_key} missing backstory"

    def test_tasks_have_required_fields(self):
        from data_pipeline_monitor.crew import _load_yaml

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

    @patch("data_pipeline_monitor.crew.Agent")
    def test_creates_all_agents(self, mock_agent_cls):
        from data_pipeline_monitor.crew import _create_agents

        mock_agent_cls.return_value = MagicMock()
        agents = _create_agents()
        assert set(agents.keys()) == set(_AGENT_KEYS)

    @patch("data_pipeline_monitor.crew.Agent")
    def test_classifier_uses_classifier_model(self, mock_agent_cls):
        from data_pipeline_monitor.crew import _create_agents

        mock_agent_cls.return_value = MagicMock()
        with patch.dict(os.environ, {"CLASSIFIER_MODEL": "gpt-4o-mini"}):
            _create_agents()

        # Find the classifier call (first call)
        calls = mock_agent_cls.call_args_list
        classifier_call = calls[0]
        assert classifier_call.kwargs["llm"] == "gpt-4o-mini"

    @patch("data_pipeline_monitor.crew.Agent")
    def test_specialists_use_main_model(self, mock_agent_cls):
        from data_pipeline_monitor.crew import _create_agents

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

    @patch("data_pipeline_monitor.crew.Task")
    def test_create_task_interpolates_query(self, mock_task_cls):
        from data_pipeline_monitor.crew import _create_task

        mock_task_cls.return_value = MagicMock()
        agent = MagicMock()
        _create_task("classify_request", agent, "ETL-003 failed")

        call_kwargs = mock_task_cls.call_args.kwargs
        assert "ETL-003 failed" in call_kwargs["description"]

    @patch("data_pipeline_monitor.crew.Task")
    def test_create_task_sets_agent(self, mock_task_cls):
        from data_pipeline_monitor.crew import _create_task

        mock_task_cls.return_value = MagicMock()
        agent = MagicMock()
        _create_task("check_pipeline", agent, "test")

        call_kwargs = mock_task_cls.call_args.kwargs
        assert call_kwargs["agent"] is agent


# ═══════════════════════════════════════════════════════════════════════════════
# 9. classify_request (mocked)
# ═══════════════════════════════════════════════════════════════════════════════


class TestClassifyRequest:
    """Test classify_request with mocked CrewAI."""

    @patch("data_pipeline_monitor.crew._create_agents")
    @patch("data_pipeline_monitor.crew.Crew")
    @patch("data_pipeline_monitor.crew._create_task")
    def test_classify_pipeline_health(self, mock_task, mock_crew_cls, mock_agents):
        from data_pipeline_monitor.crew import classify_request

        mock_agents.return_value = _mock_agents_dict()
        mock_result = MagicMock()
        mock_result.raw = "pipeline_health"
        mock_crew_cls.return_value.kickoff.return_value = mock_result

        assert classify_request("Check ETL-001 status") == "pipeline_health"

    @patch("data_pipeline_monitor.crew._create_agents")
    @patch("data_pipeline_monitor.crew.Crew")
    @patch("data_pipeline_monitor.crew._create_task")
    def test_classify_data_quality(self, mock_task, mock_crew_cls, mock_agents):
        from data_pipeline_monitor.crew import classify_request

        mock_agents.return_value = _mock_agents_dict()
        mock_result = MagicMock()
        mock_result.raw = "data_quality"
        mock_crew_cls.return_value.kickoff.return_value = mock_result

        assert classify_request("Schema drift in products") == "data_quality"

    @patch("data_pipeline_monitor.crew._create_agents")
    @patch("data_pipeline_monitor.crew.Crew")
    @patch("data_pipeline_monitor.crew._create_task")
    def test_classify_alert_management(self, mock_task, mock_crew_cls, mock_agents):
        from data_pipeline_monitor.crew import classify_request

        mock_agents.return_value = _mock_agents_dict()
        mock_result = MagicMock()
        mock_result.raw = "alert_management"
        mock_crew_cls.return_value.kickoff.return_value = mock_result

        assert classify_request("Set up PagerDuty") == "alert_management"

    @patch("data_pipeline_monitor.crew._create_agents")
    @patch("data_pipeline_monitor.crew.Crew")
    @patch("data_pipeline_monitor.crew._create_task")
    def test_classify_recovery(self, mock_task, mock_crew_cls, mock_agents):
        from data_pipeline_monitor.crew import classify_request

        mock_agents.return_value = _mock_agents_dict()
        mock_result = MagicMock()
        mock_result.raw = "recovery"
        mock_crew_cls.return_value.kickoff.return_value = mock_result

        assert classify_request("Retry failed pipeline") == "recovery"

    @patch("data_pipeline_monitor.crew._create_agents")
    @patch("data_pipeline_monitor.crew.Crew")
    @patch("data_pipeline_monitor.crew._create_task")
    def test_classify_fallback(self, mock_task, mock_crew_cls, mock_agents):
        from data_pipeline_monitor.crew import classify_request

        mock_agents.return_value = _mock_agents_dict()
        mock_result = MagicMock()
        mock_result.raw = "something random"
        mock_crew_cls.return_value.kickoff.return_value = mock_result

        assert classify_request("blah blah") == "pipeline_health"


# ═══════════════════════════════════════════════════════════════════════════════
# 10. handle_request (mocked)
# ═══════════════════════════════════════════════════════════════════════════════


class TestHandleRequest:
    """Test handle_request with mocked CrewAI."""

    @patch("data_pipeline_monitor.crew._create_agents")
    @patch("data_pipeline_monitor.crew.Crew")
    @patch("data_pipeline_monitor.crew._create_task")
    @patch("data_pipeline_monitor.crew.classify_request")
    def test_handle_pipeline_health_request(
        self, mock_classify, mock_task, mock_crew_cls, mock_agents
    ):
        from data_pipeline_monitor.crew import handle_request

        mock_classify.return_value = "pipeline_health"
        mock_agents.return_value = _mock_agents_dict()
        mock_result = MagicMock()
        mock_result.raw = "Pipeline ETL-001 is running normally..."
        mock_crew_cls.return_value.kickoff.return_value = mock_result

        result = handle_request("Check ETL-001 status")
        assert result.category == "pipeline_health"
        assert "running" in result.response.lower()

    @patch("data_pipeline_monitor.crew._create_agents")
    @patch("data_pipeline_monitor.crew.Crew")
    @patch("data_pipeline_monitor.crew._create_task")
    @patch("data_pipeline_monitor.crew.classify_request")
    def test_handle_data_quality_request(
        self, mock_classify, mock_task, mock_crew_cls, mock_agents
    ):
        from data_pipeline_monitor.crew import handle_request

        mock_classify.return_value = "data_quality"
        mock_agents.return_value = _mock_agents_dict()
        mock_result = MagicMock()
        mock_result.raw = "Schema drift detected in products table..."
        mock_crew_cls.return_value.kickoff.return_value = mock_result

        result = handle_request("Check products data quality")
        assert result.category == "data_quality"

    @patch("data_pipeline_monitor.crew._create_agents")
    @patch("data_pipeline_monitor.crew.Crew")
    @patch("data_pipeline_monitor.crew._create_task")
    @patch("data_pipeline_monitor.crew.classify_request")
    def test_handle_preserves_query(
        self, mock_classify, mock_task, mock_crew_cls, mock_agents
    ):
        from data_pipeline_monitor.crew import handle_request

        mock_classify.return_value = "alert_management"
        mock_agents.return_value = _mock_agents_dict()
        mock_result = MagicMock()
        mock_result.raw = "Configure PagerDuty integration..."
        mock_crew_cls.return_value.kickoff.return_value = mock_result

        result = handle_request("Set up PagerDuty alerts")
        assert result.query == "Set up PagerDuty alerts"

    @patch("data_pipeline_monitor.crew._create_agents")
    @patch("data_pipeline_monitor.crew.Crew")
    @patch("data_pipeline_monitor.crew._create_task")
    @patch("data_pipeline_monitor.crew.classify_request")
    def test_handle_recovery_request(
        self, mock_classify, mock_task, mock_crew_cls, mock_agents
    ):
        from data_pipeline_monitor.crew import handle_request

        mock_classify.return_value = "recovery"
        mock_agents.return_value = _mock_agents_dict()
        mock_result = MagicMock()
        mock_result.raw = "Retry with exponential backoff..."
        mock_crew_cls.return_value.kickoff.return_value = mock_result

        result = handle_request("Recover ETL-003 after failure")
        assert result.category == "recovery"


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

        args = parser.parse_args(["--query", "check pipeline status"])
        assert args.query == "check pipeline status"
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

    @patch("data_pipeline_monitor.crew.Agent")
    def test_default_model(self, mock_agent_cls):
        from data_pipeline_monitor.crew import _create_agents

        mock_agent_cls.return_value = MagicMock()
        env = {k: v for k, v in os.environ.items() if k != "MODEL"}
        with patch.dict(os.environ, env, clear=True):
            _create_agents()

        # Specialist calls should use default gpt-4o
        for call in mock_agent_cls.call_args_list[1:]:
            assert call.kwargs["llm"] == "gpt-4o"

    @patch("data_pipeline_monitor.crew.Agent")
    def test_custom_model(self, mock_agent_cls):
        from data_pipeline_monitor.crew import _create_agents

        mock_agent_cls.return_value = MagicMock()
        with patch.dict(os.environ, {"MODEL": "anthropic/claude-sonnet-4-20250514"}):
            _create_agents()

        for call in mock_agent_cls.call_args_list[1:]:
            assert call.kwargs["llm"] == "anthropic/claude-sonnet-4-20250514"

    @patch("data_pipeline_monitor.crew.Agent")
    def test_verbose_default_true(self, mock_agent_cls):
        from data_pipeline_monitor.crew import _create_agents

        mock_agent_cls.return_value = MagicMock()
        env = {k: v for k, v in os.environ.items() if k != "VERBOSE"}
        with patch.dict(os.environ, env, clear=True):
            _create_agents()

        for call in mock_agent_cls.call_args_list:
            assert call.kwargs["verbose"] is True
