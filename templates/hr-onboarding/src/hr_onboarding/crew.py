"""HR Onboarding Assistant — Crew & Flow definitions.

This module defines the multi-agent HR onboarding assistant using CrewAI.
It includes a classifier agent that routes requests to specialized agents:
- Document Collector: Handles employment contracts, tax forms, ID verification
- IT Setup Coordinator: Manages laptop provisioning, accounts, access permissions
- Training Scheduler: Plans orientation, compliance, and role-specific training
- Buddy Matcher: Assigns mentors, coordinates introductions and welcome events
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


class OnboardingResult(BaseModel):
    """Result of processing an HR onboarding request."""

    query: str
    category: Literal[
        "document_collection", "it_setup", "training_schedule", "buddy_match"
    ]
    response: str


# ─── Agent Factory ───────────────────────────────────────────────────────────


def _create_agents() -> dict[str, Agent]:
    """Create agents from YAML configuration."""
    from hr_onboarding.tools.custom_tool import (
        check_onboarding_status,
        lookup_employee,
        search_onboarding_guide,
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
        "document_collector": Agent(
            role=agents_config["document_collector"]["role"],
            goal=agents_config["document_collector"]["goal"],
            backstory=agents_config["document_collector"]["backstory"],
            tools=[search_onboarding_guide, lookup_employee],
            llm=model,
            verbose=verbose,
        ),
        "it_setup_coordinator": Agent(
            role=agents_config["it_setup_coordinator"]["role"],
            goal=agents_config["it_setup_coordinator"]["goal"],
            backstory=agents_config["it_setup_coordinator"]["backstory"],
            tools=[search_onboarding_guide, lookup_employee],
            llm=model,
            verbose=verbose,
        ),
        "training_scheduler": Agent(
            role=agents_config["training_scheduler"]["role"],
            goal=agents_config["training_scheduler"]["goal"],
            backstory=agents_config["training_scheduler"]["backstory"],
            tools=[search_onboarding_guide, check_onboarding_status],
            llm=model,
            verbose=verbose,
        ),
        "buddy_matcher": Agent(
            role=agents_config["buddy_matcher"]["role"],
            goal=agents_config["buddy_matcher"]["goal"],
            backstory=agents_config["buddy_matcher"]["backstory"],
            tools=[search_onboarding_guide, lookup_employee],
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
    """Classify an HR onboarding request.

    Returns one of: document_collection, it_setup, training_schedule, buddy_match.
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
    if "document_collection" in raw:
        return "document_collection"
    if "it_setup" in raw:
        return "it_setup"
    if "training_schedule" in raw:
        return "training_schedule"
    if "buddy_match" in raw:
        return "buddy_match"

    # Stage 2: fallback keyword match
    if any(kw in raw for kw in (
        "document", "contract", "tax", "w-4", "i-9", "bank", "payroll",
        "benefits", "enrollment", "id verification", "emergency contact",
    )):
        return "document_collection"
    if any(kw in raw for kw in (
        "laptop", "email", "account", "vpn", "badge", "software",
        "permission", "access", "it ", "computer", "setup",
    )):
        return "it_setup"
    if any(kw in raw for kw in (
        "training", "orientation", "compliance", "course", "e-learning",
        "schedule", "learn", "class", "workshop", "onboarding plan",
    )):
        return "training_schedule"
    if any(kw in raw for kw in (
        "buddy", "mentor", "introduction", "welcome", "team",
        "social", "lunch", "tour", "meet",
    )):
        return "buddy_match"

    # Default fallback
    return "document_collection"


def handle_request(query: str) -> OnboardingResult:
    """Process an HR onboarding request through the full pipeline."""
    # Step 1: Classify
    category = classify_request(query)

    # Step 2: Route to specialist
    agents = _create_agents()

    task_map = {
        "document_collection": ("collect_documents", agents["document_collector"]),
        "it_setup": ("coordinate_it_setup", agents["it_setup_coordinator"]),
        "training_schedule": ("schedule_training", agents["training_scheduler"]),
        "buddy_match": ("match_buddy", agents["buddy_matcher"]),
    }

    task_key, agent = task_map[category]
    task = _create_task(task_key, agent, query)

    crew = Crew(
        agents=[agent],
        tasks=[task],
        process=Process.sequential,
    )
    result = crew.kickoff()

    return OnboardingResult(
        query=query,
        category=category,
        response=result.raw,
    )
