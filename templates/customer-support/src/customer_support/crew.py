"""Customer Support Agent - Crew & Flow definitions.

This module defines the multi-agent customer support system using CrewAI.
It includes a classifier agent that routes inquiries to specialized agents:
- FAQ Specialist: Answers common questions from the knowledge base
- Ticket Handler: Creates structured support tickets
- Escalation Manager: Handles urgent issues requiring human intervention
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

import yaml
from crewai import Agent, Crew, Process, Task
from pydantic import BaseModel

# ─── Configuration ───────────────────────────────────────────────────────────

CONFIG_DIR = Path(__file__) / "config"


def _load_yaml(filename: str) -> dict:
    """Load a YAML configuration file."""
    filepath = Path(__file__).parent / "config" / filename
    with open(filepath, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


# ─── State ───────────────────────────────────────────────────────────────────

class SupportResult(BaseModel):
    """Result of processing a customer support inquiry."""

    query: str
    category: Literal["faq", "ticket", "escalation"]
    response: str


# ─── Agent Factory ───────────────────────────────────────────────────────────

def _create_agents() -> dict[str, Agent]:
    """Create agents from YAML configuration."""
    from customer_support.tools.custom_tool import search_knowledge_base

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
        "faq_specialist": Agent(
            role=agents_config["faq_specialist"]["role"],
            goal=agents_config["faq_specialist"]["goal"],
            backstory=agents_config["faq_specialist"]["backstory"],
            tools=[search_knowledge_base],
            llm=model,
            verbose=verbose,
        ),
        "ticket_handler": Agent(
            role=agents_config["ticket_handler"]["role"],
            goal=agents_config["ticket_handler"]["goal"],
            backstory=agents_config["ticket_handler"]["backstory"],
            llm=model,
            verbose=verbose,
        ),
        "escalation_manager": Agent(
            role=agents_config["escalation_manager"]["role"],
            goal=agents_config["escalation_manager"]["goal"],
            backstory=agents_config["escalation_manager"]["backstory"],
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

def classify_inquiry(query: str) -> str:
    """Classify a customer inquiry into faq, ticket, or escalation.

    Args:
        query: The customer's inquiry text.

    Returns:
        Classification result: 'faq', 'ticket', or 'escalation'.
    """
    agents = _create_agents()
    task = _create_task("classify_inquiry", agents["classifier"], query)

    crew = Crew(
        agents=[agents["classifier"]],
        tasks=[task],
        process=Process.sequential,
        verbose=False,
    )
    result = crew.kickoff()
    raw = result.raw.strip().lower()

    # Normalize the output
    if "faq" in raw:
        return "faq"
    elif "ticket" in raw:
        return "ticket"
    elif "escalat" in raw:
        return "escalation"
    # Default to ticket if unclear
    return "ticket"


def handle_inquiry(query: str) -> SupportResult:
    """Process a customer inquiry through the full support pipeline.

    1. Classify the inquiry (faq / ticket / escalation)
    2. Route to the appropriate specialist agent
    3. Return the structured result

    Args:
        query: The customer's inquiry text.

    Returns:
        SupportResult with category and response.
    """
    # Step 1: Classify
    category = classify_inquiry(query)

    # Step 2: Route to specialist
    agents = _create_agents()

    task_map = {
        "faq": ("answer_faq", agents["faq_specialist"]),
        "ticket": ("create_ticket", agents["ticket_handler"]),
        "escalation": ("prepare_escalation", agents["escalation_manager"]),
    }

    task_key, agent = task_map[category]
    task = _create_task(task_key, agent, query)

    crew = Crew(
        agents=[agent],
        tasks=[task],
        process=Process.sequential,
    )
    result = crew.kickoff()

    return SupportResult(
        query=query,
        category=category,
        response=result.raw,
    )
