"""E-commerce Assistant Agent - Crew & Flow definitions.

This module defines the multi-agent e-commerce assistant using CrewAI.
It includes a classifier agent that routes inquiries to specialized agents:
- Product Search: Finds and compares products from the catalog
- Order Tracker: Checks order status and shipping information
- Return Handler: Processes return and refund requests
- Recommender: Provides personalized product recommendations
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

class EcommerceResult(BaseModel):
    """Result of processing an e-commerce inquiry."""

    query: str
    category: Literal["product_search", "order_tracking", "return_refund", "recommendation"]
    response: str


# ─── Agent Factory ───────────────────────────────────────────────────────────

def _create_agents() -> dict[str, Agent]:
    """Create agents from YAML configuration."""
    from ecommerce_assistant.tools.custom_tool import lookup_order, search_product_catalog

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
        "product_search": Agent(
            role=agents_config["product_search"]["role"],
            goal=agents_config["product_search"]["goal"],
            backstory=agents_config["product_search"]["backstory"],
            tools=[search_product_catalog],
            llm=model,
            verbose=verbose,
        ),
        "order_tracker": Agent(
            role=agents_config["order_tracker"]["role"],
            goal=agents_config["order_tracker"]["goal"],
            backstory=agents_config["order_tracker"]["backstory"],
            tools=[lookup_order],
            llm=model,
            verbose=verbose,
        ),
        "return_handler": Agent(
            role=agents_config["return_handler"]["role"],
            goal=agents_config["return_handler"]["goal"],
            backstory=agents_config["return_handler"]["backstory"],
            tools=[search_product_catalog],
            llm=model,
            verbose=verbose,
        ),
        "recommender": Agent(
            role=agents_config["recommender"]["role"],
            goal=agents_config["recommender"]["goal"],
            backstory=agents_config["recommender"]["backstory"],
            tools=[search_product_catalog],
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
    """Classify an e-commerce inquiry.

    Returns one of: product_search, order_tracking, return_refund, recommendation.
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
    if "product_search" in raw or "product" in raw and "search" in raw:
        return "product_search"
    elif "order_tracking" in raw or "order" in raw and "track" in raw:
        return "order_tracking"
    elif "return_refund" in raw or "return" in raw or "refund" in raw:
        return "return_refund"
    elif "recommendation" in raw or "recommend" in raw:
        return "recommendation"
    return "product_search"  # default fallback


def handle_inquiry(query: str) -> EcommerceResult:
    """Process an e-commerce inquiry through the full assistant pipeline."""
    # Step 1: Classify
    category = classify_inquiry(query)

    # Step 2: Route to specialist
    agents = _create_agents()

    task_map = {
        "product_search": ("search_products", agents["product_search"]),
        "order_tracking": ("track_order", agents["order_tracker"]),
        "return_refund": ("process_return", agents["return_handler"]),
        "recommendation": ("recommend_products", agents["recommender"]),
    }

    task_key, agent = task_map[category]
    task = _create_task(task_key, agent, query)

    crew = Crew(
        agents=[agent],
        tasks=[task],
        process=Process.sequential,
    )
    result = crew.kickoff()

    return EcommerceResult(
        query=query,
        category=category,
        response=result.raw,
    )
