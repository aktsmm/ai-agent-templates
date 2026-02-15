"""Legal Document Analyzer Agent - Crew & Flow definitions.

This module defines the multi-agent legal document analyzer using CrewAI.
It includes a classifier agent that routes requests to specialized agents:
- Clause Extractor: Finds and presents specific contract clauses
- Risk Analyzer: Identifies legal risks and unfavorable terms
- Summarizer: Creates concise document summaries
- Comparator: Compares documents and finds differences
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

class AnalysisResult(BaseModel):
    """Result of processing a legal document analysis request."""

    query: str
    category: Literal["clause_extraction", "risk_analysis", "summarization", "comparison"]
    response: str


# ─── Agent Factory ───────────────────────────────────────────────────────────

def _create_agents() -> dict[str, Agent]:
    """Create agents from YAML configuration."""
    from legal_document_analyzer.tools.custom_tool import (
        compare_document_sections,
        get_document_sections,
        search_document_clauses,
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
        "clause_extractor": Agent(
            role=agents_config["clause_extractor"]["role"],
            goal=agents_config["clause_extractor"]["goal"],
            backstory=agents_config["clause_extractor"]["backstory"],
            tools=[search_document_clauses, get_document_sections],
            llm=model,
            verbose=verbose,
        ),
        "risk_analyzer": Agent(
            role=agents_config["risk_analyzer"]["role"],
            goal=agents_config["risk_analyzer"]["goal"],
            backstory=agents_config["risk_analyzer"]["backstory"],
            tools=[search_document_clauses, get_document_sections],
            llm=model,
            verbose=verbose,
        ),
        "summarizer": Agent(
            role=agents_config["summarizer"]["role"],
            goal=agents_config["summarizer"]["goal"],
            backstory=agents_config["summarizer"]["backstory"],
            tools=[search_document_clauses, get_document_sections],
            llm=model,
            verbose=verbose,
        ),
        "comparator": Agent(
            role=agents_config["comparator"]["role"],
            goal=agents_config["comparator"]["goal"],
            backstory=agents_config["comparator"]["backstory"],
            tools=[compare_document_sections, get_document_sections],
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
    """Classify a legal document analysis request.

    Returns one of: clause_extraction, risk_analysis, summarization, comparison.
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
    if "clause_extraction" in raw or ("clause" in raw and "extract" in raw) or "clause" in raw:
        return "clause_extraction"
    elif "risk_analysis" in raw or ("risk" in raw and "analy" in raw):
        return "risk_analysis"
    elif "summarization" in raw or "summar" in raw:
        return "summarization"
    elif "comparison" in raw or "compar" in raw:
        return "comparison"
    return "summarization"  # default fallback


def analyze_document(query: str) -> AnalysisResult:
    """Process a legal document analysis request through the full pipeline."""
    # Step 1: Classify
    category = classify_request(query)

    # Step 2: Route to specialist
    agents = _create_agents()

    task_map = {
        "clause_extraction": ("extract_clauses", agents["clause_extractor"]),
        "risk_analysis": ("analyze_risks", agents["risk_analyzer"]),
        "summarization": ("summarize_document", agents["summarizer"]),
        "comparison": ("compare_documents", agents["comparator"]),
    }

    task_key, agent = task_map[category]
    task = _create_task(task_key, agent, query)

    crew = Crew(
        agents=[agent],
        tasks=[task],
        process=Process.sequential,
    )
    result = crew.kickoff()

    return AnalysisResult(
        query=query,
        category=category,
        response=result.raw,
    )
