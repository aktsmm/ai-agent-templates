"""Content Marketing Agent - Crew & Flow definitions.

This module defines the multi-agent content marketing system using CrewAI.
It includes a classifier agent that routes requests to specialized agents:
- Content Strategist: Plans content strategy, editorial calendars, audience research
- Blog Writer: Creates blog posts, articles, and thought leadership content
- Social Media Creator: Crafts platform-specific social media content
- SEO Analyzer: Conducts keyword research, SEO audits, and optimization
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

import yaml
from crewai import Agent, Crew, Process, Task
from pydantic import BaseModel

# ─── Configuration ───────────────────────────────────────────────────────────


def _load_yaml(filename: str) -> dict:
    """Load a YAML configuration file."""
    filepath = Path(__file__).parent / "config" / filename
    with open(filepath, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


# ─── State ───────────────────────────────────────────────────────────────────


class ContentResult(BaseModel):
    """Result of processing a content marketing request."""

    query: str
    category: Literal[
        "content_strategy", "blog_writing", "social_media", "seo_analysis"
    ]
    response: str


# ─── Agent Factory ───────────────────────────────────────────────────────────


def _create_agents() -> dict[str, Agent]:
    """Create agents from YAML configuration."""
    from content_marketing.tools.custom_tool import (
        check_content_performance,
        lookup_campaign,
        search_content_guide,
    )

    agents_config = _load_yaml("agents.yaml")
    model = os.getenv("MODEL", "gpt-4o")
    classifier_model = os.getenv("CLASSIFIER_MODEL", "gpt-4o-mini")
    verbose = os.getenv("VERBOSE", "true").lower() == "true"

    return {
        "classifier": Agent(
            role=agents_config["classifier"]["role"],
            goal=agents_config["classifier"]["goal"],
            backstory=agents_config["classifier"]["backstory"],
            llm=classifier_model,
            verbose=verbose,
        ),
        "content_strategist": Agent(
            role=agents_config["content_strategist"]["role"],
            goal=agents_config["content_strategist"]["goal"],
            backstory=agents_config["content_strategist"]["backstory"],
            tools=[search_content_guide, lookup_campaign, check_content_performance],
            llm=model,
            verbose=verbose,
        ),
        "blog_writer": Agent(
            role=agents_config["blog_writer"]["role"],
            goal=agents_config["blog_writer"]["goal"],
            backstory=agents_config["blog_writer"]["backstory"],
            tools=[search_content_guide, lookup_campaign],
            llm=model,
            verbose=verbose,
        ),
        "social_media_creator": Agent(
            role=agents_config["social_media_creator"]["role"],
            goal=agents_config["social_media_creator"]["goal"],
            backstory=agents_config["social_media_creator"]["backstory"],
            tools=[search_content_guide, check_content_performance],
            llm=model,
            verbose=verbose,
        ),
        "seo_analyzer": Agent(
            role=agents_config["seo_analyzer"]["role"],
            goal=agents_config["seo_analyzer"]["goal"],
            backstory=agents_config["seo_analyzer"]["backstory"],
            tools=[search_content_guide, check_content_performance],
            llm=model,
            verbose=verbose,
        ),
    }


# ─── Task Factory ────────────────────────────────────────────────────────────


def _create_task(
    task_key: str,
    agent: Agent,
    query: str,
) -> Task:
    """Create a task from YAML configuration with query interpolation."""
    tasks_config = _load_yaml("tasks.yaml")
    task_cfg = tasks_config[task_key]

    return Task(
        description=task_cfg["description"].replace("{query}", query),
        expected_output=task_cfg["expected_output"],
        agent=agent,
    )


# ─── Main Processing Functions ───────────────────────────────────────────────


def classify_request(query: str) -> str:
    """Classify a content marketing request.

    Returns one of: content_strategy, blog_writing, social_media, seo_analysis.
    """
    agents = _create_agents()
    task = _create_task("classify_request", agents["classifier"], query)

    crew = Crew(
        agents=[agents["classifier"]],
        tasks=[task],
        process=Process.sequential,
        verbose=False,
    )
    result = crew.kickoff()
    raw = result.raw.strip().lower()

    return _normalize_category(raw)


def _normalize_category(raw: str) -> str:
    """Normalize raw classifier output to a valid category.

    Uses a two-stage matching strategy:
    1. Direct category keyword match
    2. Fallback keyword match for natural language variations
    """
    # Stage 1: direct category match
    if "content_strategy" in raw:
        return "content_strategy"
    if "blog_writing" in raw:
        return "blog_writing"
    if "social_media" in raw:
        return "social_media"
    if "seo_analysis" in raw:
        return "seo_analysis"

    # Stage 2: fallback keyword match
    if any(kw in raw for kw in (
        "strategy", "planning", "calendar", "editorial", "audit", "persona",
        "pillar", "roadmap",
    )):
        return "content_strategy"
    if any(kw in raw for kw in (
        "blog", "article", "post", "write", "writing", "draft", "copy",
        "thought leadership", "case study", "guide",
    )):
        return "blog_writing"
    if any(kw in raw for kw in (
        "social", "linkedin", "twitter", "instagram", "facebook", "hashtag",
        "caption", "reel", "carousel", "tiktok",
    )):
        return "social_media"
    if any(kw in raw for kw in (
        "seo", "keyword", "ranking", "search", "backlink", "meta",
        "serp", "organic", "crawl",
    )):
        return "seo_analysis"

    # Default fallback
    return "blog_writing"


def handle_request(query: str) -> ContentResult:
    """Process a content marketing request through the full pipeline."""
    # Step 1: Classify
    category = classify_request(query)

    # Step 2: Route to specialist
    agents = _create_agents()

    task_map = {
        "content_strategy": (
            "plan_content_strategy",
            agents["content_strategist"],
        ),
        "blog_writing": ("write_blog_post", agents["blog_writer"]),
        "social_media": (
            "create_social_content",
            agents["social_media_creator"],
        ),
        "seo_analysis": ("analyze_seo", agents["seo_analyzer"]),
    }

    task_key, agent = task_map[category]
    task = _create_task(task_key, agent, query)

    crew = Crew(
        agents=[agent],
        tasks=[task],
        process=Process.sequential,
    )
    result = crew.kickoff()

    return ContentResult(
        query=query,
        category=category,
        response=result.raw,
    )
