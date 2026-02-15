"""Tests for the subsidy consultant agent.

Covers:
- Subsidy knowledge base data integrity
- Subsidy search tool (keyword matching, edge cases)
- Pydantic result models
- Azure OpenAI LLM configuration
- YAML configuration validation
- Agent/Task factory (mocked)
- match_subsidies / draft_application / score_application integration (mocked)
- CLI argument parsing
- Environment & security checks
"""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml

# Helper: knowledge base path
_KB_PATH = (
    Path(__file__).parent.parent
    / "src" / "subsidy_consultant"
    / "knowledge" / "subsidies.yaml"
)

# Helper: all agent keys for mock setup
_AGENT_KEYS = ["matcher", "writer", "scorer", "summarizer"]


def _mock_agents_dict():
    """Create a dict of MagicMock agents for all 4 roles."""
    return {k: MagicMock() for k in _AGENT_KEYS}


# ═══════════════════════════════════════════════════════════════════════════════
# 1. Subsidy Knowledge Base
# ═══════════════════════════════════════════════════════════════════════════════


class TestSubsidyKnowledgeBase:
    """Test the subsidy knowledge base data."""

    def test_subsidies_yaml_loads(self):
        with open(_KB_PATH, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        assert "subsidies" in data
        assert len(data["subsidies"]) >= 5

    def test_each_subsidy_has_required_fields(self):
        with open(_KB_PATH, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        required = ["name", "max_amount", "subsidy_rate", "target", "purpose", "requirements"]
        for sub in data["subsidies"]:
            for field in required:
                assert field in sub, f"Missing '{field}' in {sub.get('name', 'unknown')}"

    def test_subsidy_names_are_unique(self):
        """Each subsidy should have a unique name."""
        with open(_KB_PATH, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        names = [s["name"] for s in data["subsidies"]]
        assert len(names) == len(set(names)), "Duplicate subsidy names found"


# ═══════════════════════════════════════════════════════════════════════════════
# 2. Subsidy Search Tool
# ═══════════════════════════════════════════════════════════════════════════════


class TestSubsidySearch:
    """Test the subsidy search tool."""

    def test_search_finds_manufacturing(self):
        from subsidy_consultant.tools.subsidy_search import search_subsidies
        result = search_subsidies.run("製造業")
        assert "ものづくり" in result or "補助金" in result

    def test_search_finds_it(self):
        from subsidy_consultant.tools.subsidy_search import search_subsidies
        result = search_subsidies.run("IT")
        assert "IT" in result or "補助金" in result

    def test_search_no_results(self):
        from subsidy_consultant.tools.subsidy_search import search_subsidies
        result = search_subsidies.run("xyznonexistent12345")
        assert "見つかりませんでした" in result

    def test_list_all(self):
        from subsidy_consultant.tools.subsidy_search import list_all_subsidies
        result = list_all_subsidies.run()
        assert "ものづくり" in result
        assert "持続化" in result

    def test_search_empty_query(self):
        """Empty query should not crash."""
        from subsidy_consultant.tools.subsidy_search import search_subsidies
        result = search_subsidies.run("")
        assert isinstance(result, str)


# ═══════════════════════════════════════════════════════════════════════════════
# 3. Pydantic Result Models
# ═══════════════════════════════════════════════════════════════════════════════


class TestResultModels:
    """Test Pydantic result models."""

    def test_match_result(self):
        from subsidy_consultant.crew import MatchResult
        r = MatchResult(company_info="製造業 / 30人", recommendations="ものづくり補助金を推薦")
        assert r.company_info == "製造業 / 30人"

    def test_draft_result(self):
        from subsidy_consultant.crew import DraftResult
        r = DraftResult(subsidy_name="ものづくり補助金", draft="事業計画書ドラフト...")
        assert r.subsidy_name == "ものづくり補助金"

    def test_score_result(self):
        from subsidy_consultant.crew import ScoreResult
        r = ScoreResult(subsidy_name="持続化補助金", score_report="総合スコア: 20/25")
        assert "20/25" in r.score_report

    def test_summary_result(self):
        from subsidy_consultant.crew import SummaryResult
        r = SummaryResult(summary="申請期限: 2026年3月31日")
        assert "申請期限" in r.summary

    def test_match_result_empty_fields(self):
        """Empty strings should be accepted."""
        from subsidy_consultant.crew import MatchResult
        r = MatchResult(company_info="", recommendations="")
        assert r.company_info == ""


# ═══════════════════════════════════════════════════════════════════════════════
# 4. Azure OpenAI LLM Configuration
# ═══════════════════════════════════════════════════════════════════════════════


class TestAzureLLMConfig:
    """Test Azure OpenAI configuration."""

    def test_get_azure_llm_default(self):
        from subsidy_consultant.crew import _get_azure_llm
        with patch.dict(os.environ, {"AZURE_OPENAI_DEPLOYMENT": "gpt-4o"}):
            result = _get_azure_llm(mini=False)
        assert result == "azure/gpt-4o"

    def test_get_azure_llm_mini(self):
        from subsidy_consultant.crew import _get_azure_llm
        with patch.dict(os.environ, {"AZURE_OPENAI_MINI_DEPLOYMENT": "gpt-4o-mini"}):
            result = _get_azure_llm(mini=True)
        assert result == "azure/gpt-4o-mini"

    def test_get_azure_llm_fallback(self):
        """Without env vars, should use default deployment names."""
        from subsidy_consultant.crew import _get_azure_llm
        with patch.dict(os.environ, {}, clear=True):
            result_full = _get_azure_llm(mini=False)
            result_mini = _get_azure_llm(mini=True)
        assert result_full == "azure/gpt-4o"
        assert result_mini == "azure/gpt-4o-mini"


# ═══════════════════════════════════════════════════════════════════════════════
# 5. YAML Configuration
# ═══════════════════════════════════════════════════════════════════════════════


class TestYamlConfig:
    """Test YAML configuration files are valid and complete."""

    def test_load_agents_yaml(self):
        from subsidy_consultant.crew import _load_yaml
        config = _load_yaml("agents.yaml")
        expected = ["matcher", "writer", "scorer", "summarizer"]
        for agent_key in expected:
            assert agent_key in config, f"Missing agent: {agent_key}"
            assert "role" in config[agent_key]
            assert "goal" in config[agent_key]
            assert "backstory" in config[agent_key]

    def test_load_tasks_yaml(self):
        from subsidy_consultant.crew import _load_yaml
        config = _load_yaml("tasks.yaml")
        expected = [
            "match_subsidies", "draft_application",
            "score_application", "summarize_guidelines",
        ]
        for task_key in expected:
            assert task_key in config, f"Missing task: {task_key}"
            assert "description" in config[task_key]
            assert "expected_output" in config[task_key]

    def test_load_nonexistent_yaml_raises(self):
        from subsidy_consultant.crew import _load_yaml
        with pytest.raises(FileNotFoundError):
            _load_yaml("nonexistent.yaml")


# ═══════════════════════════════════════════════════════════════════════════════
# 6. Agent Factory (mocked)
# ═══════════════════════════════════════════════════════════════════════════════


class TestAgentFactory:
    """Test agent creation from YAML config (mocked to avoid LLM calls)."""

    @patch("subsidy_consultant.crew.Agent")
    def test_creates_four_agents(self, mock_agent_cls):
        from subsidy_consultant.crew import _create_agents
        agents = _create_agents()
        assert len(agents) == 4
        assert set(agents.keys()) == {"matcher", "writer", "scorer", "summarizer"}

    @patch("subsidy_consultant.crew.Agent")
    def test_matcher_uses_mini_model(self, mock_agent_cls):
        """Matcher should use the cheaper mini model."""
        from subsidy_consultant.crew import _create_agents
        with patch.dict(os.environ, {"AZURE_OPENAI_MINI_DEPLOYMENT": "gpt-4o-mini"}):
            _create_agents()
        # First call = matcher, should use mini
        calls = mock_agent_cls.call_args_list
        assert calls[0].kwargs.get("llm") == "azure/gpt-4o-mini"


# ═══════════════════════════════════════════════════════════════════════════════
# 7. Integration Tests (mocked CrewAI)
# ═══════════════════════════════════════════════════════════════════════════════


class TestMatchSubsidies:
    """Test match_subsidies with mocked CrewAI."""

    @patch("subsidy_consultant.crew._create_task", return_value=MagicMock())
    @patch("subsidy_consultant.crew._create_agents")
    @patch("subsidy_consultant.crew.Crew")
    def test_match_returns_result(self, mock_crew_cls, mock_agents, mock_task):
        from subsidy_consultant.crew import MatchResult, match_subsidies

        mock_agents.return_value = _mock_agents_dict()
        mock_result = MagicMock()
        mock_result.raw = (
            "ものづくり補助金、IT導入補助金、事業再構築補助金を推薦"
        )
        mock_crew_cls.return_value.kickoff.return_value = mock_result

        result = match_subsidies(
            industry="製造業",
            employees=30,
            capital="3,000万円",
            location="東京都",
            challenge="生産ラインの自動化",
        )
        assert isinstance(result, MatchResult)
        assert "製造業" in result.company_info
        assert "ものづくり" in result.recommendations


class TestDraftApplication:
    """Test draft_application with mocked CrewAI."""

    @patch("subsidy_consultant.crew._create_task", return_value=MagicMock())
    @patch("subsidy_consultant.crew._create_agents")
    @patch("subsidy_consultant.crew.Crew")
    def test_draft_returns_result(self, mock_crew_cls, mock_agents, mock_task):
        from subsidy_consultant.crew import DraftResult, draft_application

        mock_agents.return_value = _mock_agents_dict()
        mock_result = MagicMock()
        mock_result.raw = (
            "【事業計画書】AI外観検査装置の導入による生産性向上"
        )
        mock_crew_cls.return_value.kickoff.return_value = mock_result

        result = draft_application(
            subsidy_name="ものづくり補助金",
            company_info="製造業、従業員30名",
            plan_summary="AI外観検査装置の導入",
        )
        assert isinstance(result, DraftResult)
        assert result.subsidy_name == "ものづくり補助金"
        assert "事業計画" in result.draft


class TestScoreApplication:
    """Test score_application with mocked CrewAI."""

    @patch("subsidy_consultant.crew._create_task", return_value=MagicMock())
    @patch("subsidy_consultant.crew._create_agents")
    @patch("subsidy_consultant.crew.Crew")
    def test_score_returns_result(self, mock_crew_cls, mock_agents, mock_task):
        from subsidy_consultant.crew import ScoreResult, score_application

        mock_agents.return_value = _mock_agents_dict()
        mock_result = MagicMock()
        mock_result.raw = "総合スコア: 22/25 — 採択可能性: 高"
        mock_crew_cls.return_value.kickoff.return_value = mock_result

        result = score_application(
            subsidy_name="ものづくり補助金",
            application_text="テスト申請書本文",
        )
        assert isinstance(result, ScoreResult)
        assert "22/25" in result.score_report


# ═══════════════════════════════════════════════════════════════════════════════
# 8. CLI Argument Parsing
# ═══════════════════════════════════════════════════════════════════════════════


class TestCLI:
    """Test CLI argument parsing (no LLM calls)."""

    def test_parse_match_command(self):
        import argparse
        parser = argparse.ArgumentParser()
        sub = parser.add_subparsers(dest="command")
        mp = sub.add_parser("match")
        mp.add_argument("--industry", "-i", required=True)
        mp.add_argument("--employees", "-e", type=int, required=True)
        mp.add_argument("--capital", "-c", required=True)
        mp.add_argument("--location", "-l", required=True)
        mp.add_argument("--challenge", required=True)

        args = parser.parse_args([
            "match", "-i", "IT", "-e", "10",
            "-c", "1000万円", "-l", "東京都",
            "--challenge", "DX推進",
        ])
        assert args.command == "match"
        assert args.industry == "IT"
        assert args.employees == 10

    def test_parse_draft_command(self):
        import argparse
        parser = argparse.ArgumentParser()
        sub = parser.add_subparsers(dest="command")
        dp = sub.add_parser("draft")
        dp.add_argument("--subsidy", "-s", required=True)
        dp.add_argument("--company", required=True)
        dp.add_argument("--plan", required=True)

        args = parser.parse_args([
            "draft", "-s", "ものづくり補助金",
            "--company", "製造業", "--plan", "設備投資",
        ])
        assert args.command == "draft"
        assert args.subsidy == "ものづくり補助金"


# ═══════════════════════════════════════════════════════════════════════════════
# 9. Environment & Security Checks
# ═══════════════════════════════════════════════════════════════════════════════


class TestEnvConfig:
    """Test environment variable configuration."""

    def test_env_example_exists(self):
        env_example = Path(__file__).parent.parent / ".env.example"
        assert env_example.exists(), ".env.example is required for template users"

    def test_env_example_contains_required_vars(self):
        env_example = Path(__file__).parent.parent / ".env.example"
        content = env_example.read_text(encoding="utf-8")
        required = ["AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_API_KEY", "AZURE_OPENAI_DEPLOYMENT"]
        for var in required:
            assert var in content, f".env.example missing {var}"

    def test_gitignore_excludes_env(self):
        gitignore = Path(__file__).parent.parent / ".gitignore"
        content = gitignore.read_text(encoding="utf-8")
        assert ".env" in content
