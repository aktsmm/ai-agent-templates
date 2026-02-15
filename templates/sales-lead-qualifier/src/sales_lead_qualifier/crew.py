"""Sales Lead Qualifier Agent - Crew & Flow definitions.

This module defines the multi-agent sales lead qualifier using CrewAI.
It includes a classifier agent that routes requests to specialized agents:
- Lead Scorer: Evaluates leads using BANT framework (Budget, Authority, Need, Timeline)
- Company Researcher: Provides comprehensive company intelligence
- Email Composer: Crafts personalized sales outreach emails
- Objection Handler: Prepares responses to sales objections
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

class SalesResult(BaseModel):
    """Result of processing a sales request."""

    query: str
    category: Literal["lead_scoring", "company_research", "email_outreach", "objection_handling"]
    response: str


# ─── Agent Factory ───────────────────────────────────────────────────────────

def _create_agents() -> dict[str, Agent]:
    """Create agents from YAML configuration."""
    from sales_lead_qualifier.tools.custom_tool import lookup_company, search_lead_database

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
        "lead_scorer": Agent(
            role=agents_config["lead_scorer"]["role"],
            goal=agents_config["lead_scorer"]["goal"],
            backstory=agents_config["lead_scorer"]["backstory"],
            tools=[search_lead_database, lookup_company],
            llm=model,
            verbose=verbose,
        ),
        "company_researcher": Agent(
            role=agents_config["company_researcher"]["role"],
            goal=agents_config["company_researcher"]["goal"],
            backstory=agents_config["company_researcher"]["backstory"],
            tools=[search_lead_database, lookup_company],
            llm=model,
            verbose=verbose,
        ),
        "email_composer": Agent(
            role=agents_config["email_composer"]["role"],
            goal=agents_config["email_composer"]["goal"],
            backstory=agents_config["email_composer"]["backstory"],
            tools=[search_lead_database, lookup_company],
            llm=model,
            verbose=verbose,
        ),
        "objection_handler": Agent(
            role=agents_config["objection_handler"]["role"],
            goal=agents_config["objection_handler"]["goal"],
            backstory=agents_config["objection_handler"]["backstory"],
            tools=[search_lead_database],
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
    """Classify a sales request.

    Returns one of: lead_scoring, company_research, email_outreach, objection_handling.
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

    # Normalize the output
    if "lead_scoring" in raw or ("lead" in raw and "scor" in raw):
        return "lead_scoring"
    elif "company_research" in raw or ("company" in raw and "research" in raw):
        return "company_research"
    elif "email_outreach" in raw or "email" in raw and ("outreach" in raw or "compose" in raw):
        return "email_outreach"
    elif "objection_handling" in raw or "objection" in raw:
        return "objection_handling"
    elif "qualify" in raw or "bant" in raw or "score" in raw:
        return "lead_scoring"
    elif "research" in raw or "intel" in raw:
        return "company_research"
    elif "email" in raw or "write" in raw or "draft" in raw:
        return "email_outreach"
    return "lead_scoring"  # default fallback


def handle_request(query: str) -> SalesResult:
    """Process a sales request through the full pipeline."""
    # Step 1: Classify
    category = classify_request(query)

    # Step 2: Route to specialist
    agents = _create_agents()

    task_map = {
        "lead_scoring": ("score_lead", agents["lead_scorer"]),
        "company_research": ("research_company", agents["company_researcher"]),
        "email_outreach": ("compose_email", agents["email_composer"]),
        "objection_handling": ("handle_objection", agents["objection_handler"]),
    }

    task_key, agent = task_map[category]
    task = _create_task(task_key, agent, query)

    crew = Crew(
        agents=[agent],
        tasks=[task],
        process=Process.sequential,
    )
    result = crew.kickoff()

    return SalesResult(
        query=query,
        category=category,
        response=result.raw,
    )
