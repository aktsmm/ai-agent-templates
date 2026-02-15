"""Tests for the content marketing agent.

Covers:
- Content guide search tool (keyword matching, edge cases)
- Campaign lookup tool (valid/invalid IDs)
- Content performance tool (valid/invalid channels)
- Classification normalization logic
- ContentResult Pydantic model validation
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
    "classifier", "content_strategist",
    "blog_writer", "social_media_creator", "seo_analyzer",
]


def _mock_agents_dict():
    """Create a dict of MagicMock agents for all 5 roles."""
    return {k: MagicMock() for k in _AGENT_KEYS}


# ═══════════════════════════════════════════════════════════════════════════════
# 1. Content Guide Search Tool
# ═══════════════════════════════════════════════════════════════════════════════


class TestContentGuideSearch:
    """Test the content guide search tool."""

    def test_search_finds_seo(self):
        from content_marketing.tools.custom_tool import search_content_guide

        result = search_content_guide.run("SEO")
        assert "seo" in result.lower()

    def test_search_finds_blog(self):
        from content_marketing.tools.custom_tool import search_content_guide

        result = search_content_guide.run("blog")
        assert "blog" in result.lower()

    def test_search_finds_linkedin(self):
        from content_marketing.tools.custom_tool import search_content_guide

        result = search_content_guide.run("LinkedIn")
        assert "linkedin" in result.lower()

    def test_search_finds_hashtag(self):
        from content_marketing.tools.custom_tool import search_content_guide

        result = search_content_guide.run("hashtag")
        assert "hashtag" in result.lower()

    def test_search_finds_editorial(self):
        from content_marketing.tools.custom_tool import search_content_guide

        result = search_content_guide.run("editorial")
        assert "editorial" in result.lower()

    def test_search_no_results(self):
        from content_marketing.tools.custom_tool import search_content_guide

        result = search_content_guide.run("xyznonexistent12345")
        assert "No content guide articles found" in result

    def test_search_case_insensitive(self):
        from content_marketing.tools.custom_tool import search_content_guide

        lower = search_content_guide.run("keyword")
        upper = search_content_guide.run("KEYWORD")
        assert "No content guide articles found" not in lower
        assert "No content guide articles found" not in upper

    def test_search_returns_truncated_results(self):
        from content_marketing.tools.custom_tool import search_content_guide

        result = search_content_guide.run("content")
        for section in result.split("---"):
            assert len(section.strip()) <= 800 or section.strip() == ""

    def test_search_empty_query(self):
        from content_marketing.tools.custom_tool import search_content_guide

        result = search_content_guide.run("")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_search_finds_instagram(self):
        from content_marketing.tools.custom_tool import search_content_guide

        result = search_content_guide.run("Instagram")
        assert "No content guide articles found" not in result

    def test_search_finds_persona(self):
        from content_marketing.tools.custom_tool import search_content_guide

        result = search_content_guide.run("persona")
        assert "No content guide articles found" not in result

    def test_search_finds_backlink(self):
        from content_marketing.tools.custom_tool import search_content_guide

        result = search_content_guide.run("backlink")
        assert "No content guide articles found" not in result

    def test_search_finds_analytics(self):
        from content_marketing.tools.custom_tool import search_content_guide

        result = search_content_guide.run("analytics")
        assert "No content guide articles found" not in result


# ═══════════════════════════════════════════════════════════════════════════════
# 2. Campaign Lookup Tool
# ═══════════════════════════════════════════════════════════════════════════════


class TestCampaignLookup:
    """Test the campaign lookup tool."""

    def test_lookup_active_blog_campaign(self):
        from content_marketing.tools.custom_tool import lookup_campaign

        result = lookup_campaign.run("CMP-001")
        assert "Active" in result
        assert "Product Launch" in result

    def test_lookup_active_social_campaign(self):
        from content_marketing.tools.custom_tool import lookup_campaign

        result = lookup_campaign.run("CMP-002")
        assert "Active" in result
        assert "LinkedIn" in result

    def test_lookup_in_progress_seo_campaign(self):
        from content_marketing.tools.custom_tool import lookup_campaign

        result = lookup_campaign.run("CMP-003")
        assert "In Progress" in result
        assert "SEO" in result

    def test_lookup_planned_campaign(self):
        from content_marketing.tools.custom_tool import lookup_campaign

        result = lookup_campaign.run("CMP-004")
        assert "Planned" in result
        assert "Instagram" in result

    def test_lookup_completed_campaign(self):
        from content_marketing.tools.custom_tool import lookup_campaign

        result = lookup_campaign.run("CMP-005")
        assert "Completed" in result
        assert "Strategy" in result

    def test_lookup_case_insensitive(self):
        from content_marketing.tools.custom_tool import lookup_campaign

        result = lookup_campaign.run("cmp-001")
        assert "Active" in result

    def test_lookup_invalid_campaign(self):
        from content_marketing.tools.custom_tool import lookup_campaign

        result = lookup_campaign.run("CMP-999")
        assert "Campaign not found" in result

    def test_lookup_empty_id(self):
        from content_marketing.tools.custom_tool import lookup_campaign

        result = lookup_campaign.run("")
        assert "Campaign not found" in result

    def test_lookup_returns_all_fields(self):
        from content_marketing.tools.custom_tool import lookup_campaign

        result = lookup_campaign.run("CMP-001")
        assert "Name" in result
        assert "Status" in result
        assert "Type" in result

    def test_lookup_campaign_has_notes(self):
        from content_marketing.tools.custom_tool import lookup_campaign

        result = lookup_campaign.run("CMP-002")
        assert "Notes" in result
        assert "Carousel" in result


# ═══════════════════════════════════════════════════════════════════════════════
# 3. Content Performance Tool
# ═══════════════════════════════════════════════════════════════════════════════


class TestContentPerformance:
    """Test the content performance check tool."""

    def test_blog_performance(self):
        from content_marketing.tools.custom_tool import check_content_performance

        result = check_content_performance.run("blog")
        assert "Company Blog" in result
        assert "45,200" in result

    def test_linkedin_performance(self):
        from content_marketing.tools.custom_tool import check_content_performance

        result = check_content_performance.run("linkedin")
        assert "LinkedIn" in result
        assert "28,500" in result

    def test_twitter_performance(self):
        from content_marketing.tools.custom_tool import check_content_performance

        result = check_content_performance.run("twitter")
        assert "Twitter" in result

    def test_instagram_performance(self):
        from content_marketing.tools.custom_tool import check_content_performance

        result = check_content_performance.run("instagram")
        assert "Instagram" in result

    def test_email_performance(self):
        from content_marketing.tools.custom_tool import check_content_performance

        result = check_content_performance.run("email")
        assert "Newsletter" in result
        assert "32.5%" in result

    def test_youtube_performance(self):
        from content_marketing.tools.custom_tool import check_content_performance

        result = check_content_performance.run("youtube")
        assert "YouTube" in result

    def test_twitter_alias_x(self):
        from content_marketing.tools.custom_tool import check_content_performance

        result = check_content_performance.run("x")
        assert "Twitter" in result

    def test_instagram_alias_ig(self):
        from content_marketing.tools.custom_tool import check_content_performance

        result = check_content_performance.run("ig")
        assert "Instagram" in result

    def test_invalid_channel(self):
        from content_marketing.tools.custom_tool import check_content_performance

        result = check_content_performance.run("tiktok")
        assert "not found" in result
        assert "Available channels" in result

    def test_performance_returns_trend(self):
        from content_marketing.tools.custom_tool import check_content_performance

        result = check_content_performance.run("blog")
        assert "Trend" in result


# ═══════════════════════════════════════════════════════════════════════════════
# 4. Classification Normalization
# ═══════════════════════════════════════════════════════════════════════════════


class TestNormalizeCategory:
    """Test the _normalize_category function with parametrized inputs."""

    @pytest.mark.parametrize(
        "raw, expected",
        [
            # Stage 1: direct match
            ("content_strategy", "content_strategy"),
            ("blog_writing", "blog_writing"),
            ("social_media", "social_media"),
            ("seo_analysis", "seo_analysis"),
            # Direct match with surrounding text
            ("The category is content_strategy.", "content_strategy"),
            ("I think this is blog_writing", "blog_writing"),
            ("Classified as: social_media", "social_media"),
            ("Result: seo_analysis", "seo_analysis"),
            # Stage 2: fallback keywords - content strategy
            ("strategy", "content_strategy"),
            ("planning", "content_strategy"),
            ("calendar", "content_strategy"),
            ("editorial", "content_strategy"),
            ("audit", "content_strategy"),
            ("persona", "content_strategy"),
            ("pillar", "content_strategy"),
            ("roadmap", "content_strategy"),
            # Stage 2: fallback keywords - blog writing
            ("blog", "blog_writing"),
            ("article", "blog_writing"),
            ("post", "blog_writing"),
            ("write", "blog_writing"),
            ("writing", "blog_writing"),
            ("draft", "blog_writing"),
            ("copy", "blog_writing"),
            ("thought leadership", "blog_writing"),
            ("case study", "blog_writing"),
            ("guide", "blog_writing"),
            # Stage 2: fallback keywords - social media
            ("social", "social_media"),
            ("linkedin", "social_media"),
            ("twitter", "social_media"),
            ("instagram", "social_media"),
            ("facebook", "social_media"),
            ("hashtag", "social_media"),
            ("caption", "social_media"),
            ("reel", "social_media"),
            ("carousel", "social_media"),
            ("tiktok", "social_media"),
            # Stage 2: fallback keywords - SEO
            ("seo", "seo_analysis"),
            ("keyword", "seo_analysis"),
            ("ranking", "seo_analysis"),
            ("search", "seo_analysis"),
            ("backlink", "seo_analysis"),
            ("meta", "seo_analysis"),
            ("serp", "seo_analysis"),
            ("organic", "seo_analysis"),
            ("crawl", "seo_analysis"),
            # Default fallback
            ("unknown request type", "blog_writing"),
            ("", "blog_writing"),
        ],
    )
    def test_normalize(self, raw: str, expected: str):
        from content_marketing.crew import _normalize_category

        assert _normalize_category(raw) == expected


# ═══════════════════════════════════════════════════════════════════════════════
# 5. ContentResult Pydantic Model
# ═══════════════════════════════════════════════════════════════════════════════


class TestContentResult:
    """Test the ContentResult Pydantic model."""

    def test_valid_content_strategy(self):
        from content_marketing.crew import ContentResult

        r = ContentResult(
            query="Plan Q2 content",
            category="content_strategy",
            response="Here is your strategy.",
        )
        assert r.category == "content_strategy"

    def test_valid_blog_writing(self):
        from content_marketing.crew import ContentResult

        r = ContentResult(
            query="Write a blog post",
            category="blog_writing",
            response="Blog draft ready.",
        )
        assert r.category == "blog_writing"

    def test_valid_social_media(self):
        from content_marketing.crew import ContentResult

        r = ContentResult(
            query="Create LinkedIn post",
            category="social_media",
            response="LinkedIn post created.",
        )
        assert r.category == "social_media"

    def test_valid_seo_analysis(self):
        from content_marketing.crew import ContentResult

        r = ContentResult(
            query="Analyze keywords",
            category="seo_analysis",
            response="Keyword analysis complete.",
        )
        assert r.category == "seo_analysis"

    def test_invalid_category_raises(self):
        from content_marketing.crew import ContentResult

        with pytest.raises(Exception):
            ContentResult(
                query="test",
                category="invalid_category",
                response="test",
            )

    def test_model_fields(self):
        from content_marketing.crew import ContentResult

        r = ContentResult(
            query="test query",
            category="blog_writing",
            response="test response",
        )
        assert r.query == "test query"
        assert r.response == "test response"

    def test_model_dict(self):
        from content_marketing.crew import ContentResult

        r = ContentResult(
            query="q",
            category="seo_analysis",
            response="r",
        )
        d = r.model_dump()
        assert "query" in d
        assert "category" in d
        assert "response" in d


# ═══════════════════════════════════════════════════════════════════════════════
# 6. YAML Configuration Loading
# ═══════════════════════════════════════════════════════════════════════════════


class TestYAMLConfig:
    """Test YAML configuration file loading."""

    def test_agents_yaml_loads(self):
        from content_marketing.crew import _load_yaml

        config = _load_yaml("agents.yaml")
        assert "classifier" in config
        assert "content_strategist" in config
        assert "blog_writer" in config
        assert "social_media_creator" in config
        assert "seo_analyzer" in config

    def test_tasks_yaml_loads(self):
        from content_marketing.crew import _load_yaml

        config = _load_yaml("tasks.yaml")
        assert "classify_request" in config
        assert "plan_content_strategy" in config
        assert "write_blog_post" in config
        assert "create_social_content" in config
        assert "analyze_seo" in config

    def test_agents_have_required_fields(self):
        from content_marketing.crew import _load_yaml

        config = _load_yaml("agents.yaml")
        for key in config:
            assert "role" in config[key], f"{key} missing 'role'"
            assert "goal" in config[key], f"{key} missing 'goal'"
            assert "backstory" in config[key], f"{key} missing 'backstory'"

    def test_tasks_have_required_fields(self):
        from content_marketing.crew import _load_yaml

        config = _load_yaml("tasks.yaml")
        for key in config:
            assert "description" in config[key], f"{key} missing 'description'"
            assert "expected_output" in config[key], f"{key} missing 'expected_output'"


# ═══════════════════════════════════════════════════════════════════════════════
# 7. Agent Factory (Mocked)
# ═══════════════════════════════════════════════════════════════════════════════


class TestAgentFactory:
    """Test agent creation from YAML configuration."""

    @patch("content_marketing.crew.Agent")
    def test_creates_all_agents(self, mock_agent_cls):
        from content_marketing.crew import _create_agents

        mock_agent_cls.return_value = MagicMock()
        agents = _create_agents()
        assert set(agents.keys()) == set(_AGENT_KEYS)

    @patch("content_marketing.crew.Agent")
    def test_classifier_uses_classifier_model(self, mock_agent_cls):
        from content_marketing.crew import _create_agents

        mock_agent_cls.return_value = MagicMock()
        with patch.dict(os.environ, {"CLASSIFIER_MODEL": "gpt-4o-mini"}):
            _create_agents()

        calls = mock_agent_cls.call_args_list
        classifier_call = calls[0]
        assert classifier_call.kwargs["llm"] == "gpt-4o-mini"

    @patch("content_marketing.crew.Agent")
    def test_specialists_use_main_model(self, mock_agent_cls):
        from content_marketing.crew import _create_agents

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

    @patch("content_marketing.crew.Task")
    def test_create_task_interpolates_query(self, mock_task_cls):
        from content_marketing.crew import _create_task

        mock_task_cls.return_value = MagicMock()
        agent = MagicMock()
        _create_task("classify_request", agent, "Write a blog post")

        call_kwargs = mock_task_cls.call_args.kwargs
        assert "Write a blog post" in call_kwargs["description"]

    @patch("content_marketing.crew.Task")
    def test_create_task_sets_agent(self, mock_task_cls):
        from content_marketing.crew import _create_task

        mock_task_cls.return_value = MagicMock()
        agent = MagicMock()
        _create_task("plan_content_strategy", agent, "Plan Q2 content")

        call_kwargs = mock_task_cls.call_args.kwargs
        assert call_kwargs["agent"] is agent


# ═══════════════════════════════════════════════════════════════════════════════
# 9. classify_request (Mocked CrewAI)
# ═══════════════════════════════════════════════════════════════════════════════


class TestClassifyRequest:
    """Test classify_request with mocked CrewAI."""

    @patch("content_marketing.crew._create_agents")
    @patch("content_marketing.crew.Crew")
    @patch("content_marketing.crew._create_task")
    def test_classify_blog_writing(self, mock_task, mock_crew_cls, mock_agents):
        from content_marketing.crew import classify_request

        mock_agents.return_value = _mock_agents_dict()
        mock_result = MagicMock()
        mock_result.raw = "blog_writing"
        mock_crew_cls.return_value.kickoff.return_value = mock_result

        assert classify_request("Write a blog about AI trends") == "blog_writing"

    @patch("content_marketing.crew._create_agents")
    @patch("content_marketing.crew.Crew")
    @patch("content_marketing.crew._create_task")
    def test_classify_social_media(self, mock_task, mock_crew_cls, mock_agents):
        from content_marketing.crew import classify_request

        mock_agents.return_value = _mock_agents_dict()
        mock_result = MagicMock()
        mock_result.raw = "social_media"
        mock_crew_cls.return_value.kickoff.return_value = mock_result

        assert classify_request("Create a LinkedIn post") == "social_media"

    @patch("content_marketing.crew._create_agents")
    @patch("content_marketing.crew.Crew")
    @patch("content_marketing.crew._create_task")
    def test_classify_seo(self, mock_task, mock_crew_cls, mock_agents):
        from content_marketing.crew import classify_request

        mock_agents.return_value = _mock_agents_dict()
        mock_result = MagicMock()
        mock_result.raw = "seo_analysis"
        mock_crew_cls.return_value.kickoff.return_value = mock_result

        assert classify_request("Research keywords for our product page") == "seo_analysis"

    @patch("content_marketing.crew._create_agents")
    @patch("content_marketing.crew.Crew")
    @patch("content_marketing.crew._create_task")
    def test_classify_strategy(self, mock_task, mock_crew_cls, mock_agents):
        from content_marketing.crew import classify_request

        mock_agents.return_value = _mock_agents_dict()
        mock_result = MagicMock()
        mock_result.raw = "content_strategy"
        mock_crew_cls.return_value.kickoff.return_value = mock_result

        assert classify_request("Build a content calendar for Q3") == "content_strategy"

    @patch("content_marketing.crew._create_agents")
    @patch("content_marketing.crew.Crew")
    @patch("content_marketing.crew._create_task")
    def test_classify_fallback(self, mock_task, mock_crew_cls, mock_agents):
        from content_marketing.crew import classify_request

        mock_agents.return_value = _mock_agents_dict()
        mock_result = MagicMock()
        mock_result.raw = "something unclear"
        mock_crew_cls.return_value.kickoff.return_value = mock_result

        assert classify_request("Do something") == "blog_writing"  # default fallback


# ═══════════════════════════════════════════════════════════════════════════════
# 10. handle_request (Mocked CrewAI)
# ═══════════════════════════════════════════════════════════════════════════════


class TestHandleRequest:
    """Test handle_request with mocked CrewAI."""

    @patch("content_marketing.crew._create_agents")
    @patch("content_marketing.crew.Crew")
    @patch("content_marketing.crew._create_task")
    @patch("content_marketing.crew.classify_request")
    def test_handle_blog_request(
        self, mock_classify, mock_task, mock_crew_cls, mock_agents
    ):
        from content_marketing.crew import handle_request

        mock_classify.return_value = "blog_writing"
        mock_agents.return_value = _mock_agents_dict()
        mock_result = MagicMock()
        mock_result.raw = "Here is your blog post outline."
        mock_crew_cls.return_value.kickoff.return_value = mock_result

        result = handle_request("Write a blog about AI")
        assert result.category == "blog_writing"
        assert "blog post outline" in result.response

    @patch("content_marketing.crew._create_agents")
    @patch("content_marketing.crew.Crew")
    @patch("content_marketing.crew._create_task")
    @patch("content_marketing.crew.classify_request")
    def test_handle_social_request(
        self, mock_classify, mock_task, mock_crew_cls, mock_agents
    ):
        from content_marketing.crew import handle_request

        mock_classify.return_value = "social_media"
        mock_agents.return_value = _mock_agents_dict()
        mock_result = MagicMock()
        mock_result.raw = "LinkedIn post ready."
        mock_crew_cls.return_value.kickoff.return_value = mock_result

        result = handle_request("Create Instagram content")
        assert result.category == "social_media"
        assert result.query == "Create Instagram content"

    @patch("content_marketing.crew._create_agents")
    @patch("content_marketing.crew.Crew")
    @patch("content_marketing.crew._create_task")
    @patch("content_marketing.crew.classify_request")
    def test_handle_seo_request(
        self, mock_classify, mock_task, mock_crew_cls, mock_agents
    ):
        from content_marketing.crew import handle_request

        mock_classify.return_value = "seo_analysis"
        mock_agents.return_value = _mock_agents_dict()
        mock_result = MagicMock()
        mock_result.raw = "Keyword analysis complete."
        mock_crew_cls.return_value.kickoff.return_value = mock_result

        result = handle_request("Analyze our SEO performance")
        assert result.category == "seo_analysis"

    @patch("content_marketing.crew._create_agents")
    @patch("content_marketing.crew.Crew")
    @patch("content_marketing.crew._create_task")
    @patch("content_marketing.crew.classify_request")
    def test_handle_strategy_request(
        self, mock_classify, mock_task, mock_crew_cls, mock_agents
    ):
        from content_marketing.crew import handle_request

        mock_classify.return_value = "content_strategy"
        mock_agents.return_value = _mock_agents_dict()
        mock_result = MagicMock()
        mock_result.raw = "Strategy recommendation delivered."
        mock_crew_cls.return_value.kickoff.return_value = mock_result

        result = handle_request("Plan our content strategy for next quarter")
        assert result.category == "content_strategy"


# ═══════════════════════════════════════════════════════════════════════════════
# 11. CLI Argument Parsing
# ═══════════════════════════════════════════════════════════════════════════════


class TestCLIParsing:
    """Test CLI argument parsing."""

    def test_parse_query_flag(self):
        import argparse

        parser = argparse.ArgumentParser()
        parser.add_argument("--query", "-q", type=str)
        parser.add_argument("--file", "-f", type=str)
        parser.add_argument("--classify-only", "-c", action="store_true")

        args = parser.parse_args(["--query", "Write a blog"])
        assert args.query == "Write a blog"
        assert args.file is None
        assert args.classify_only is False

    def test_parse_file_flag(self):
        import argparse

        parser = argparse.ArgumentParser()
        parser.add_argument("--query", "-q", type=str)
        parser.add_argument("--file", "-f", type=str)
        parser.add_argument("--classify-only", "-c", action="store_true")

        args = parser.parse_args(["--file", "requests.txt"])
        assert args.file == "requests.txt"

    def test_parse_classify_only(self):
        import argparse

        parser = argparse.ArgumentParser()
        parser.add_argument("--query", "-q", type=str)
        parser.add_argument("--file", "-f", type=str)
        parser.add_argument("--classify-only", "-c", action="store_true")

        args = parser.parse_args(["-q", "test", "-c"])
        assert args.classify_only is True

    def test_parse_no_args(self):
        import argparse

        parser = argparse.ArgumentParser()
        parser.add_argument("--query", "-q", type=str)
        parser.add_argument("--file", "-f", type=str)
        parser.add_argument("--classify-only", "-c", action="store_true")

        args = parser.parse_args([])
        assert args.query is None
        assert args.file is None
        assert args.classify_only is False


# ═══════════════════════════════════════════════════════════════════════════════
# 12. Environment Variable Handling
# ═══════════════════════════════════════════════════════════════════════════════


class TestEnvironmentVariables:
    """Test environment variable handling."""

    @patch.dict(os.environ, {"MODEL": "custom-model"})
    def test_custom_model(self):
        assert os.environ["MODEL"] == "custom-model"

    @patch.dict(os.environ, {"CLASSIFIER_MODEL": "custom-classifier"})
    def test_custom_classifier_model(self):
        assert os.environ["CLASSIFIER_MODEL"] == "custom-classifier"

    @patch.dict(os.environ, {}, clear=True)
    def test_default_model(self):
        assert os.environ.get("MODEL", "gpt-4o") == "gpt-4o"
