"""Data Pipeline Monitor — Crew & Flow definitions.

This module defines the multi-agent data pipeline monitor using CrewAI.
It includes a classifier agent that routes requests to specialized agents:
- Pipeline Health Checker: Monitors execution status, latency, throughput
- Data Quality Analyzer: Checks completeness, freshness, schema drift, anomalies
- Alert Manager: Manages alert routing, escalation, notification channels
- Recovery Advisor: Recommends recovery actions, rollback, retry strategies
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


class DataPipelineResult(BaseModel):
    """Result of processing a data pipeline monitoring request."""

    query: str
    category: Literal[
        "pipeline_health", "data_quality", "alert_management", "recovery"
    ]
    response: str


# ─── Agent Factory ───────────────────────────────────────────────────────────


def _create_agents() -> dict[str, Agent]:
    """Create agents from YAML configuration."""
    from data_pipeline_monitor.tools.custom_tool import (
        check_pipeline_status,
        query_data_metrics,
        search_runbook,
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
        "pipeline_health_checker": Agent(
            role=agents_config["pipeline_health_checker"]["role"],
            goal=agents_config["pipeline_health_checker"]["goal"],
            backstory=agents_config["pipeline_health_checker"]["backstory"],
            tools=[check_pipeline_status, search_runbook],
            llm=model,
            verbose=verbose,
        ),
        "data_quality_analyzer": Agent(
            role=agents_config["data_quality_analyzer"]["role"],
            goal=agents_config["data_quality_analyzer"]["goal"],
            backstory=agents_config["data_quality_analyzer"]["backstory"],
            tools=[query_data_metrics, search_runbook],
            llm=model,
            verbose=verbose,
        ),
        "alert_manager": Agent(
            role=agents_config["alert_manager"]["role"],
            goal=agents_config["alert_manager"]["goal"],
            backstory=agents_config["alert_manager"]["backstory"],
            tools=[search_runbook],
            llm=model,
            verbose=verbose,
        ),
        "recovery_advisor": Agent(
            role=agents_config["recovery_advisor"]["role"],
            goal=agents_config["recovery_advisor"]["goal"],
            backstory=agents_config["recovery_advisor"]["backstory"],
            tools=[check_pipeline_status, search_runbook],
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
    """Classify a data pipeline monitoring request.

    Returns one of: pipeline_health, data_quality, alert_management, recovery.
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
    if "pipeline_health" in raw:
        return "pipeline_health"
    if "data_quality" in raw:
        return "data_quality"
    if "alert_management" in raw:
        return "alert_management"
    if "recovery" in raw:
        return "recovery"

    # Stage 2: fallback keyword match
    keywords: dict[str, list[str]] = {
        "pipeline_health": [
            "pipeline", "etl", "job", "run", "execution", "status",
            "latency", "throughput", "schedule", "dag", "airflow", "orchestr",
        ],
        "data_quality": [
            "quality", "completeness", "freshness", "schema", "drift",
            "null", "duplicate", "anomal", "accuracy", "validation", "data check",
        ],
        "alert_management": [
            "alert", "notify", "notification", "escalat", "pager",
            "incident", "sla", "severity", "on-call", "channel",
        ],
        "recovery": [
            "recover", "retry", "rollback", "backfill", "restart",
            "fix", "restor", "failover", "fallback", "manual",
        ],
    }

    for category, kw_list in keywords.items():
        if any(kw in raw for kw in kw_list):
            return category

    # Default fallback
    return "pipeline_health"


def handle_request(query: str) -> DataPipelineResult:
    """Process a data pipeline monitoring request through the full pipeline."""
    # Step 1: Classify
    category = classify_request(query)

    # Step 2: Route to specialist
    agents = _create_agents()

    task_map: dict[str, tuple[str, Agent]] = {
        "pipeline_health": ("check_pipeline", agents["pipeline_health_checker"]),
        "data_quality": ("analyze_data_quality", agents["data_quality_analyzer"]),
        "alert_management": ("manage_alerts", agents["alert_manager"]),
        "recovery": ("advise_recovery", agents["recovery_advisor"]),
    }

    task_key, agent = task_map[category]
    task = _create_task(task_key, agent, query)

    crew = Crew(
        agents=[agent],
        tasks=[task],
        process=Process.sequential,
    )
    result = crew.kickoff()

    return DataPipelineResult(
        query=query,
        category=category,
        response=result.raw,
    )
