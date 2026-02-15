"""Subsidy Consultant - Multi-agent grant application assistant.

Uses Azure AI Foundry (Azure OpenAI) as the LLM backend.
Agents: Matcher, Writer, Scorer, Summarizer.
"""

from __future__ import annotations

import os
from pathlib import Path

import yaml
from crewai import Agent, Crew, Process, Task
from pydantic import BaseModel

# ─── Configuration ───────────────────────────────────────────────────────────

def _load_yaml(filename: str) -> dict:
    """Load a YAML configuration file."""
    filepath = Path(__file__).parent / "config" / filename
    with open(filepath, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _get_azure_llm(mini: bool = False) -> str:
    """Build the Azure OpenAI LLM connection string for CrewAI.

    CrewAI supports Azure OpenAI natively via the 'azure/' prefix.
    Set the following environment variables:
      - AZURE_OPENAI_ENDPOINT
      - AZURE_OPENAI_API_KEY
      - AZURE_OPENAI_DEPLOYMENT (or AZURE_OPENAI_MINI_DEPLOYMENT)
      - AZURE_OPENAI_API_VERSION
    """
    if mini:
        deployment = os.getenv("AZURE_OPENAI_MINI_DEPLOYMENT", "gpt-4o-mini")
    else:
        deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")

    # CrewAI format: "azure/<deployment-name>"
    return f"azure/{deployment}"


# ─── Result Models ───────────────────────────────────────────────────────────

class MatchResult(BaseModel):
    """Result of subsidy matching."""
    company_info: str
    recommendations: str


class DraftResult(BaseModel):
    """Result of application draft generation."""
    subsidy_name: str
    draft: str


class ScoreResult(BaseModel):
    """Result of application scoring."""
    subsidy_name: str
    score_report: str


class SummaryResult(BaseModel):
    """Result of guidelines summarization."""
    summary: str


# ─── Agent Factory ───────────────────────────────────────────────────────────

def _create_agents() -> dict[str, Agent]:
    """Create agents from YAML config with Azure OpenAI backend."""
    from subsidy_consultant.tools.subsidy_search import (
        list_all_subsidies,
        search_subsidies,
    )

    agents_config = _load_yaml("agents.yaml")
    llm = _get_azure_llm(mini=False)
    llm_mini = _get_azure_llm(mini=True)
    verbose = os.getenv("VERBOSE", "true").lower() == "true"

    return {
        "matcher": Agent(
            role=agents_config["matcher"]["role"],
            goal=agents_config["matcher"]["goal"],
            backstory=agents_config["matcher"]["backstory"],
            tools=[search_subsidies, list_all_subsidies],
            llm=llm_mini,  # マッチングは軽量モデルでOK
            verbose=verbose,
        ),
        "writer": Agent(
            role=agents_config["writer"]["role"],
            goal=agents_config["writer"]["goal"],
            backstory=agents_config["writer"]["backstory"],
            tools=[search_subsidies],
            llm=llm,  # 文章生成は高品質モデル
            verbose=verbose,
        ),
        "scorer": Agent(
            role=agents_config["scorer"]["role"],
            goal=agents_config["scorer"]["goal"],
            backstory=agents_config["scorer"]["backstory"],
            tools=[search_subsidies],
            llm=llm,
            verbose=verbose,
        ),
        "summarizer": Agent(
            role=agents_config["summarizer"]["role"],
            goal=agents_config["summarizer"]["goal"],
            backstory=agents_config["summarizer"]["backstory"],
            llm=llm_mini,
            verbose=verbose,
        ),
    }


# ─── Task Factory ────────────────────────────────────────────────────────────

def _create_task(task_key: str, agent: Agent, **kwargs: str) -> Task:
    """Create a task from YAML config with variable interpolation."""
    tasks_config = _load_yaml("tasks.yaml")
    task_cfg = tasks_config[task_key]

    description = task_cfg["description"]
    for key, value in kwargs.items():
        description = description.replace(f"{{{key}}}", value)

    return Task(
        description=description,
        expected_output=task_cfg["expected_output"],
        agent=agent,
    )


# ─── Public API ──────────────────────────────────────────────────────────────

def match_subsidies(
    industry: str,
    employees: int,
    capital: str,
    location: str,
    challenge: str,
) -> MatchResult:
    """Find matching subsidies for a company.

    Args:
        industry: 業種（例: 製造業、IT、飲食業）
        employees: 従業員数
        capital: 資本金（例: 1,000万円）
        location: 所在地（例: 東京都）
        challenge: 課題・投資計画

    Returns:
        MatchResult with recommended subsidies.
    """
    agents = _create_agents()
    task = _create_task(
        "match_subsidies",
        agents["matcher"],
        industry=industry,
        employees=str(employees),
        capital=capital,
        location=location,
        challenge=challenge,
    )

    crew = Crew(
        agents=[agents["matcher"]],
        tasks=[task],
        process=Process.sequential,
    )
    result = crew.kickoff()

    return MatchResult(
        company_info=f"{industry} / {employees}人 / {capital} / {location}",
        recommendations=result.raw,
    )


def draft_application(
    subsidy_name: str,
    company_info: str,
    plan_summary: str,
) -> DraftResult:
    """Generate a draft application (business plan) for a subsidy.

    Args:
        subsidy_name: 補助金名（例: ものづくり補助金）
        company_info: 企業の基本情報
        plan_summary: 事業計画の概要

    Returns:
        DraftResult with the drafted application.
    """
    agents = _create_agents()
    task = _create_task(
        "draft_application",
        agents["writer"],
        subsidy_name=subsidy_name,
        company_info=company_info,
        plan_summary=plan_summary,
    )

    crew = Crew(
        agents=[agents["writer"]],
        tasks=[task],
        process=Process.sequential,
    )
    result = crew.kickoff()

    return DraftResult(
        subsidy_name=subsidy_name,
        draft=result.raw,
    )


def score_application(
    subsidy_name: str,
    application_text: str,
) -> ScoreResult:
    """Score a draft application against review criteria.

    Args:
        subsidy_name: 補助金名
        application_text: 申請書の本文

    Returns:
        ScoreResult with scoring and improvement suggestions.
    """
    agents = _create_agents()
    task = _create_task(
        "score_application",
        agents["scorer"],
        subsidy_name=subsidy_name,
        application_text=application_text,
    )

    crew = Crew(
        agents=[agents["scorer"]],
        tasks=[task],
        process=Process.sequential,
    )
    result = crew.kickoff()

    return ScoreResult(
        subsidy_name=subsidy_name,
        score_report=result.raw,
    )


def summarize_guidelines(guidelines_text: str) -> SummaryResult:
    """Summarize a subsidy's application guidelines.

    Args:
        guidelines_text: 公募要領のテキスト

    Returns:
        SummaryResult with structured summary.
    """
    agents = _create_agents()
    task = _create_task(
        "summarize_guidelines",
        agents["summarizer"],
        guidelines_text=guidelines_text,
    )

    crew = Crew(
        agents=[agents["summarizer"]],
        tasks=[task],
        process=Process.sequential,
    )
    result = crew.kickoff()

    return SummaryResult(summary=result.raw)
