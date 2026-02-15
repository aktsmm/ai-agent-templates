"""IT Helpdesk Agent - Crew & Flow definitions.

This module defines the multi-agent IT helpdesk using CrewAI.
It includes a classifier agent that routes requests to specialized agents:
- Password Reset: Handles password, account lockout, and MFA issues
- Software Troubleshooter: Diagnoses software installation and crash issues
- Network Support: Resolves connectivity, VPN, and Wi-Fi problems
- Hardware Support: Handles laptop, printer, and peripheral issues
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


class HelpdeskResult(BaseModel):
    """Result of processing an IT support request."""

    query: str
    category: Literal[
        "password_reset", "software_issue", "network_issue", "hardware_issue"
    ]
    response: str


# ─── Agent Factory ───────────────────────────────────────────────────────────


def _create_agents() -> dict[str, Agent]:
    """Create agents from YAML configuration."""
    from it_helpdesk.tools.custom_tool import (
        check_system_status,
        lookup_ticket,
        search_knowledge_base,
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
        "password_reset": Agent(
            role=agents_config["password_reset"]["role"],
            goal=agents_config["password_reset"]["goal"],
            backstory=agents_config["password_reset"]["backstory"],
            tools=[search_knowledge_base, lookup_ticket],
            llm=model,
            verbose=verbose,
        ),
        "software_troubleshooter": Agent(
            role=agents_config["software_troubleshooter"]["role"],
            goal=agents_config["software_troubleshooter"]["goal"],
            backstory=agents_config["software_troubleshooter"]["backstory"],
            tools=[search_knowledge_base, lookup_ticket],
            llm=model,
            verbose=verbose,
        ),
        "network_support": Agent(
            role=agents_config["network_support"]["role"],
            goal=agents_config["network_support"]["goal"],
            backstory=agents_config["network_support"]["backstory"],
            tools=[search_knowledge_base, check_system_status],
            llm=model,
            verbose=verbose,
        ),
        "hardware_support": Agent(
            role=agents_config["hardware_support"]["role"],
            goal=agents_config["hardware_support"]["goal"],
            backstory=agents_config["hardware_support"]["backstory"],
            tools=[search_knowledge_base, lookup_ticket],
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
    """Classify an IT support request.

    Returns one of: password_reset, software_issue, network_issue, hardware_issue.
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
    if "password_reset" in raw:
        return "password_reset"
    if "software_issue" in raw:
        return "software_issue"
    if "network_issue" in raw:
        return "network_issue"
    if "hardware_issue" in raw:
        return "hardware_issue"

    # Stage 2: fallback keyword match
    if any(kw in raw for kw in ("password", "lockout", "locked", "mfa", "login")):
        return "password_reset"
    if any(kw in raw for kw in ("software", "install", "crash", "update", "app")):
        return "software_issue"
    if any(kw in raw for kw in (
        "network", "vpn", "wifi", "wi-fi", "internet", "dns", "connectivity",
    )):
        return "network_issue"
    if any(kw in raw for kw in (
        "hardware", "laptop", "printer", "monitor", "keyboard", "mouse",
    )):
        return "hardware_issue"

    # Default fallback
    return "software_issue"


def handle_request(query: str) -> HelpdeskResult:
    """Process an IT support request through the full helpdesk pipeline."""
    # Step 1: Classify
    category = classify_request(query)

    # Step 2: Route to specialist
    agents = _create_agents()

    task_map = {
        "password_reset": ("reset_password", agents["password_reset"]),
        "software_issue": (
            "troubleshoot_software",
            agents["software_troubleshooter"],
        ),
        "network_issue": ("diagnose_network", agents["network_support"]),
        "hardware_issue": ("handle_hardware", agents["hardware_support"]),
    }

    task_key, agent = task_map[category]
    task = _create_task(task_key, agent, query)

    crew = Crew(
        agents=[agent],
        tasks=[task],
        process=Process.sequential,
    )
    result = crew.kickoff()

    return HelpdeskResult(
        query=query,
        category=category,
        response=result.raw,
    )
