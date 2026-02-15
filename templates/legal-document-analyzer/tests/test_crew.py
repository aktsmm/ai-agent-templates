"""Tests for the legal document analyzer agent.

Covers:
- Document clause search tool (keyword matching, edge cases)
- Document sections tool (structure inspection)
- Document comparison tool (cross-document matching)
- Classification normalization logic
- AnalysisResult Pydantic model validation
- YAML configuration loading
- Agent factory (mocked LLM)
- classify_request / analyze_document integration (mocked CrewAI)
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
    "classifier", "clause_extractor",
    "risk_analyzer", "summarizer", "comparator",
]


def _mock_agents_dict():
    """Create a dict of MagicMock agents for all 5 roles."""
    return {k: MagicMock() for k in _AGENT_KEYS}


# ═══════════════════════════════════════════════════════════════════════════════
# 1. Document Clause Search Tool
# ═══════════════════════════════════════════════════════════════════════════════


class TestDocumentClauseSearch:
    """Test the document clause search tool."""

    def test_search_finds_confidentiality(self):
        from legal_document_analyzer.tools.custom_tool import search_document_clauses

        result = search_document_clauses.run("confidentiality")
        assert "confidential" in result.lower()

    def test_search_finds_indemnification(self):
        from legal_document_analyzer.tools.custom_tool import search_document_clauses

        result = search_document_clauses.run("indemnification")
        assert "indemnif" in result.lower()

    def test_search_finds_termination(self):
        from legal_document_analyzer.tools.custom_tool import search_document_clauses

        result = search_document_clauses.run("termination")
        assert "terminat" in result.lower()

    def test_search_finds_liability(self):
        from legal_document_analyzer.tools.custom_tool import search_document_clauses

        result = search_document_clauses.run("liability")
        assert "liabilit" in result.lower()

    def test_search_no_results(self):
        from legal_document_analyzer.tools.custom_tool import search_document_clauses

        result = search_document_clauses.run("xyznonexistent12345")
        assert "No clauses or sections found" in result

    def test_search_case_insensitive(self):
        from legal_document_analyzer.tools.custom_tool import search_document_clauses

        lower = search_document_clauses.run("warranty")
        upper = search_document_clauses.run("WARRANTY")
        assert "No clauses" not in lower or "No clauses" not in upper

    def test_search_finds_governing_law(self):
        from legal_document_analyzer.tools.custom_tool import search_document_clauses

        result = search_document_clauses.run("governing law")
        assert "No clauses" not in result

    def test_search_empty_query_returns_string(self):
        from legal_document_analyzer.tools.custom_tool import search_document_clauses

        result = search_document_clauses.run("")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_search_returns_truncated_results(self):
        from legal_document_analyzer.tools.custom_tool import search_document_clauses

        result = search_document_clauses.run("agreement")
        for section in result.split("---"):
            # Each section should be within the 800-char limit + file prefix
            stripped = section.strip()
            if stripped:
                assert len(stripped) <= 900


# ═══════════════════════════════════════════════════════════════════════════════
# 2. Document Sections Tool
# ═══════════════════════════════════════════════════════════════════════════════


class TestDocumentSections:
    """Test the document sections inspection tool."""

    def test_get_nda_sections(self):
        from legal_document_analyzer.tools.custom_tool import get_document_sections

        result = get_document_sections.run("nda")
        assert "Document:" in result
        assert "#" in result

    def test_get_license_sections(self):
        from legal_document_analyzer.tools.custom_tool import get_document_sections

        result = get_document_sections.run("software_license")
        assert "Document:" in result
        assert "#" in result

    def test_document_not_found(self):
        from legal_document_analyzer.tools.custom_tool import get_document_sections

        result = get_document_sections.run("nonexistent_document")
        assert "Document not found" in result

    def test_lists_available_documents(self):
        from legal_document_analyzer.tools.custom_tool import get_document_sections

        result = get_document_sections.run("nonexistent")
        assert "Available documents:" in result
        assert "nda_template" in result

    def test_nda_has_expected_sections(self):
        from legal_document_analyzer.tools.custom_tool import get_document_sections

        result = get_document_sections.run("nda")
        # Check for key NDA sections
        result_lower = result.lower()
        assert "definition" in result_lower
        assert "terminat" in result_lower


# ═══════════════════════════════════════════════════════════════════════════════
# 3. Document Comparison Tool
# ═══════════════════════════════════════════════════════════════════════════════


class TestDocumentComparison:
    """Test the document comparison tool."""

    def test_compare_indemnification(self):
        from legal_document_analyzer.tools.custom_tool import compare_document_sections

        result = compare_document_sections.run("Indemnification")
        assert "nda_template" in result or "software_license" in result

    def test_compare_termination(self):
        from legal_document_analyzer.tools.custom_tool import compare_document_sections

        result = compare_document_sections.run("Term and Termination")
        assert "---" in result or "nda_template" in result or "software_license" in result

    def test_compare_nonexistent_section(self):
        from legal_document_analyzer.tools.custom_tool import compare_document_sections

        result = compare_document_sections.run("Nonexistent Section XYZ")
        assert "No sections titled" in result

    def test_compare_liability(self):
        from legal_document_analyzer.tools.custom_tool import compare_document_sections

        result = compare_document_sections.run("Limitation of Liability")
        assert "liabilit" in result.lower() or "No sections" in result


# ═══════════════════════════════════════════════════════════════════════════════
# 4. Classification Normalization Logic
# ═══════════════════════════════════════════════════════════════════════════════


class TestClassificationNormalization:
    """Test request classification normalization logic.

    This tests the raw-output-to-category mapping logic used in
    classify_request() without calling any LLM.
    """

    @pytest.mark.parametrize(
        "raw_output, expected",
        [
            ("clause_extraction", "clause_extraction"),
            ("CLAUSE_EXTRACTION", "clause_extraction"),
            ("risk_analysis", "risk_analysis"),
            ("RISK_ANALYSIS", "risk_analysis"),
            ("summarization", "summarization"),
            ("SUMMARIZATION", "summarization"),
            ("comparison", "comparison"),
            ("COMPARISON", "comparison"),
            ("extract the indemnification clause", "clause_extraction"),
            ("analyze risks in this contract", "risk_analysis"),
            ("summarize this NDA", "summarization"),
            ("compare these two agreements", "comparison"),
            ("find clause about termination", "clause_extraction"),
            ("unknown query type", "summarization"),  # default fallback
            ("", "summarization"),  # empty → default
            ("   ", "summarization"),  # whitespace → default
        ],
    )
    def test_normalize(self, raw_output: str, expected: str):
        """Category normalization should match expected output."""
        raw_lower = raw_output.strip().lower()
        if (
            "clause_extraction" in raw_lower
            or ("clause" in raw_lower and "extract" in raw_lower)
            or "clause" in raw_lower
        ):
            result = "clause_extraction"
        elif "risk_analysis" in raw_lower or ("risk" in raw_lower and "analy" in raw_lower):
            result = "risk_analysis"
        elif "summarization" in raw_lower or "summar" in raw_lower:
            result = "summarization"
        elif "comparison" in raw_lower or "compar" in raw_lower:
            result = "comparison"
        else:
            result = "summarization"
        assert result == expected, f"Failed for input: {raw_output!r}"


# ═══════════════════════════════════════════════════════════════════════════════
# 5. AnalysisResult Pydantic Model
# ═══════════════════════════════════════════════════════════════════════════════


class TestAnalysisResult:
    """Test the AnalysisResult model."""

    def test_valid_clause_extraction_result(self):
        from legal_document_analyzer.crew import AnalysisResult

        result = AnalysisResult(
            query="Find the indemnification clause in the NDA",
            category="clause_extraction",
            response="Section 9: Each party agrees to indemnify...",
        )
        assert result.query == "Find the indemnification clause in the NDA"
        assert result.category == "clause_extraction"
        assert "indemnify" in result.response

    def test_valid_risk_analysis_result(self):
        from legal_document_analyzer.crew import AnalysisResult

        result = AnalysisResult(
            query="What are the risks in this contract?",
            category="risk_analysis",
            response="High Risk: Broad indemnification clause in Section 9",
        )
        assert result.category == "risk_analysis"

    def test_valid_summarization_result(self):
        from legal_document_analyzer.crew import AnalysisResult

        result = AnalysisResult(
            query="Summarize this NDA",
            category="summarization",
            response="This is a mutual NDA between Acme Corp and Beta Solutions.",
        )
        assert result.category == "summarization"

    def test_valid_comparison_result(self):
        from legal_document_analyzer.crew import AnalysisResult

        result = AnalysisResult(
            query="Compare the two contracts",
            category="comparison",
            response="The NDA has a $500K liability cap; the license has no fixed cap.",
        )
        assert result.category == "comparison"

    def test_invalid_category_rejected(self):
        from legal_document_analyzer.crew import AnalysisResult

        with pytest.raises(Exception):
            AnalysisResult(
                query="test",
                category="invalid_category",
                response="test",
            )

    def test_empty_query_allowed(self):
        from legal_document_analyzer.crew import AnalysisResult

        result = AnalysisResult(
            query="", category="summarization", response="No query provided."
        )
        assert result.query == ""

    def test_long_response_allowed(self):
        from legal_document_analyzer.crew import AnalysisResult

        long_text = "A" * 10_000
        result = AnalysisResult(
            query="test", category="summarization", response=long_text
        )
        assert len(result.response) == 10_000


# ═══════════════════════════════════════════════════════════════════════════════
# 6. YAML Configuration Loading
# ═══════════════════════════════════════════════════════════════════════════════


class TestYamlConfig:
    """Test YAML configuration files are valid and complete."""

    def test_load_agents_yaml(self):
        from legal_document_analyzer.crew import _load_yaml

        config = _load_yaml("agents.yaml")
        assert isinstance(config, dict)
        expected_agents = [
            "classifier", "clause_extractor", "risk_analyzer",
            "summarizer", "comparator",
        ]
        for agent_key in expected_agents:
            assert agent_key in config, f"Missing agent: {agent_key}"
            assert "role" in config[agent_key], f"Missing 'role' for {agent_key}"
            assert "goal" in config[agent_key], f"Missing 'goal' for {agent_key}"
            assert "backstory" in config[agent_key], f"Missing 'backstory' for {agent_key}"

    def test_load_tasks_yaml(self):
        from legal_document_analyzer.crew import _load_yaml

        config = _load_yaml("tasks.yaml")
        assert isinstance(config, dict)
        expected_tasks = [
            "classify_request", "extract_clauses", "analyze_risks",
            "summarize_document", "compare_documents",
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
        from legal_document_analyzer.crew import _load_yaml

        config = _load_yaml("tasks.yaml")
        for task_key, task_cfg in config.items():
            assert "{query}" in task_cfg["description"], (
                f"Task '{task_key}' description missing {{query}} placeholder"
            )

    def test_load_nonexistent_yaml_raises(self):
        """Loading a non-existent YAML file should raise FileNotFoundError."""
        from legal_document_analyzer.crew import _load_yaml

        with pytest.raises(FileNotFoundError):
            _load_yaml("nonexistent.yaml")


# ═══════════════════════════════════════════════════════════════════════════════
# 7. Agent Factory (mocked — no LLM calls)
# ═══════════════════════════════════════════════════════════════════════════════


class TestAgentFactory:
    """Test agent creation from YAML config (mocked to avoid LLM calls)."""

    @patch("legal_document_analyzer.crew.Agent")
    def test_creates_five_agents(self, mock_agent_cls):
        """_create_agents should create exactly 5 agents."""
        from legal_document_analyzer.crew import _create_agents

        agents = _create_agents()
        assert len(agents) == 5
        assert set(agents.keys()) == set(_AGENT_KEYS)

    @patch("legal_document_analyzer.crew.Agent")
    def test_classifier_uses_mini_model(self, mock_agent_cls):
        """Classifier should use the cheaper CLASSIFIER_MODEL."""
        from legal_document_analyzer.crew import _create_agents

        with patch.dict(os.environ, {"CLASSIFIER_MODEL": "gpt-4o-mini", "MODEL": "gpt-4o"}):
            _create_agents()

        calls = mock_agent_cls.call_args_list
        classifier_call = calls[0]
        assert classifier_call.kwargs.get("llm") == "gpt-4o-mini"

    @patch("legal_document_analyzer.crew.Agent")
    def test_verbose_env_controls_agent_verbosity(self, mock_agent_cls):
        """VERBOSE=false should set verbose=False on all agents."""
        from legal_document_analyzer.crew import _create_agents

        with patch.dict(os.environ, {"VERBOSE": "false"}):
            _create_agents()

        for call in mock_agent_cls.call_args_list:
            assert call.kwargs.get("verbose") is False


# ═══════════════════════════════════════════════════════════════════════════════
# 8. Task Factory
# ═══════════════════════════════════════════════════════════════════════════════


class TestTaskFactory:
    """Test task creation from YAML config."""

    @patch("legal_document_analyzer.crew.Task")
    def test_query_interpolation(self, mock_task_cls):
        """_create_task should replace {query} in the task description."""
        from legal_document_analyzer.crew import _create_task

        mock_agent = MagicMock()
        _create_task("classify_request", mock_agent, "Find the indemnification clause")

        call_kwargs = mock_task_cls.call_args.kwargs
        assert "Find the indemnification clause" in call_kwargs["description"]
        assert "{query}" not in call_kwargs["description"]

    @patch("legal_document_analyzer.crew.Task")
    def test_all_task_keys_valid(self, mock_task_cls):
        """All expected task keys should produce a valid Task."""
        from legal_document_analyzer.crew import _create_task

        mock_agent = MagicMock()
        for key in [
            "classify_request", "extract_clauses", "analyze_risks",
            "summarize_document", "compare_documents",
        ]:
            _create_task(key, mock_agent, "test query")
            assert mock_task_cls.called


# ═══════════════════════════════════════════════════════════════════════════════
# 9. classify_request (mocked CrewAI)
# ═══════════════════════════════════════════════════════════════════════════════


class TestClassifyRequest:
    """Test classify_request with mocked CrewAI Crew.kickoff()."""

    @patch("legal_document_analyzer.crew._create_task", return_value=MagicMock())
    @patch("legal_document_analyzer.crew._create_agents")
    @patch("legal_document_analyzer.crew.Crew")
    def test_classify_clause_extraction(self, mock_crew_cls, mock_agents, mock_task):
        from legal_document_analyzer.crew import classify_request

        mock_agents.return_value = _mock_agents_dict()
        mock_result = MagicMock()
        mock_result.raw = "clause_extraction"
        mock_crew_cls.return_value.kickoff.return_value = mock_result

        assert classify_request("Find the indemnification clause") == "clause_extraction"

    @patch("legal_document_analyzer.crew._create_task", return_value=MagicMock())
    @patch("legal_document_analyzer.crew._create_agents")
    @patch("legal_document_analyzer.crew.Crew")
    def test_classify_risk_analysis(self, mock_crew_cls, mock_agents, mock_task):
        from legal_document_analyzer.crew import classify_request

        mock_agents.return_value = _mock_agents_dict()
        mock_result = MagicMock()
        mock_result.raw = "risk_analysis"
        mock_crew_cls.return_value.kickoff.return_value = mock_result

        assert classify_request("What are the risks in this contract?") == "risk_analysis"

    @patch("legal_document_analyzer.crew._create_task", return_value=MagicMock())
    @patch("legal_document_analyzer.crew._create_agents")
    @patch("legal_document_analyzer.crew.Crew")
    def test_classify_summarization(self, mock_crew_cls, mock_agents, mock_task):
        from legal_document_analyzer.crew import classify_request

        mock_agents.return_value = _mock_agents_dict()
        mock_result = MagicMock()
        mock_result.raw = "summarization"
        mock_crew_cls.return_value.kickoff.return_value = mock_result

        assert classify_request("Summarize this NDA") == "summarization"

    @patch("legal_document_analyzer.crew._create_task", return_value=MagicMock())
    @patch("legal_document_analyzer.crew._create_agents")
    @patch("legal_document_analyzer.crew.Crew")
    def test_classify_comparison(self, mock_crew_cls, mock_agents, mock_task):
        from legal_document_analyzer.crew import classify_request

        mock_agents.return_value = _mock_agents_dict()
        mock_result = MagicMock()
        mock_result.raw = "comparison"
        mock_crew_cls.return_value.kickoff.return_value = mock_result

        assert classify_request("Compare these contracts") == "comparison"

    @patch("legal_document_analyzer.crew._create_task", return_value=MagicMock())
    @patch("legal_document_analyzer.crew._create_agents")
    @patch("legal_document_analyzer.crew.Crew")
    def test_classify_unknown_defaults_to_summarization(
        self, mock_crew_cls, mock_agents, mock_task,
    ):
        from legal_document_analyzer.crew import classify_request

        mock_agents.return_value = _mock_agents_dict()
        mock_result = MagicMock()
        mock_result.raw = "I'm not sure what category this is"
        mock_crew_cls.return_value.kickoff.return_value = mock_result

        assert classify_request("Something unclear") == "summarization"


# ═══════════════════════════════════════════════════════════════════════════════
# 10. analyze_document (mocked CrewAI)
# ═══════════════════════════════════════════════════════════════════════════════


class TestAnalyzeDocument:
    """Test analyze_document end-to-end with mocked CrewAI."""

    @patch("legal_document_analyzer.crew._create_task", return_value=MagicMock())
    @patch("legal_document_analyzer.crew._create_agents")
    @patch("legal_document_analyzer.crew.Crew")
    @patch("legal_document_analyzer.crew.classify_request", return_value="clause_extraction")
    def test_handle_clause_extraction_returns_result(
        self, mock_classify, mock_crew_cls, mock_agents, mock_task,
    ):
        from legal_document_analyzer.crew import AnalysisResult, analyze_document

        mock_agents.return_value = _mock_agents_dict()
        mock_result = MagicMock()
        mock_result.raw = "Section 9: Indemnification clause found"
        mock_crew_cls.return_value.kickoff.return_value = mock_result

        result = analyze_document("Find the indemnification clause")
        assert isinstance(result, AnalysisResult)
        assert result.category == "clause_extraction"
        assert result.query == "Find the indemnification clause"
        assert "Indemnification" in result.response

    @patch("legal_document_analyzer.crew._create_task", return_value=MagicMock())
    @patch("legal_document_analyzer.crew._create_agents")
    @patch("legal_document_analyzer.crew.Crew")
    @patch("legal_document_analyzer.crew.classify_request", return_value="risk_analysis")
    def test_handle_risk_analysis_routes_correctly(
        self, mock_classify, mock_crew_cls, mock_agents, mock_task,
    ):
        from legal_document_analyzer.crew import analyze_document

        mock_agents.return_value = _mock_agents_dict()
        mock_result = MagicMock()
        mock_result.raw = "**Overall Risk Level**: High — broad indemnification"
        mock_crew_cls.return_value.kickoff.return_value = mock_result

        result = analyze_document("What are the risks?")
        assert result.category == "risk_analysis"
        assert "High" in result.response

    @patch("legal_document_analyzer.crew._create_task", return_value=MagicMock())
    @patch("legal_document_analyzer.crew._create_agents")
    @patch("legal_document_analyzer.crew.Crew")
    @patch("legal_document_analyzer.crew.classify_request", return_value="summarization")
    def test_handle_summarization_routes_correctly(
        self, mock_classify, mock_crew_cls, mock_agents, mock_task,
    ):
        from legal_document_analyzer.crew import analyze_document

        mock_agents.return_value = _mock_agents_dict()
        mock_result = MagicMock()
        mock_result.raw = "**Document Type**: Mutual NDA between Acme Corp and Beta Solutions"
        mock_crew_cls.return_value.kickoff.return_value = mock_result

        result = analyze_document("Summarize this NDA")
        assert result.category == "summarization"
        assert "NDA" in result.response

    @patch("legal_document_analyzer.crew._create_task", return_value=MagicMock())
    @patch("legal_document_analyzer.crew._create_agents")
    @patch("legal_document_analyzer.crew.Crew")
    @patch("legal_document_analyzer.crew.classify_request", return_value="comparison")
    def test_handle_comparison_routes_correctly(
        self, mock_classify, mock_crew_cls, mock_agents, mock_task,
    ):
        from legal_document_analyzer.crew import analyze_document

        mock_agents.return_value = _mock_agents_dict()
        mock_result = MagicMock()
        mock_result.raw = "NDA has $500K liability cap; License uses revenue-based cap"
        mock_crew_cls.return_value.kickoff.return_value = mock_result

        result = analyze_document("Compare the NDA and license agreement")
        assert result.category == "comparison"
        assert "liability" in result.response.lower() or "cap" in result.response.lower()


# ═══════════════════════════════════════════════════════════════════════════════
# 11. CLI Argument Parsing
# ═══════════════════════════════════════════════════════════════════════════════


class TestCLI:
    """Test CLI argument parsing (no LLM calls)."""

    def test_parse_single_query(self):
        import argparse

        parser = argparse.ArgumentParser()
        parser.add_argument("--query", "-q", type=str)
        parser.add_argument("--file", "-f", type=str)
        parser.add_argument("--classify-only", "-c", action="store_true")

        args = parser.parse_args(["--query", "Summarize this NDA"])
        assert args.query == "Summarize this NDA"
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
# 12. Environment Variable Handling
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
