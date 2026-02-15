"""Subsidy search tool - searches the knowledge base for matching grants."""

from __future__ import annotations

from pathlib import Path

import yaml
from crewai.tools import tool


def _load_subsidies() -> list[dict]:
    """Load subsidy data from YAML knowledge base."""
    kb_path = Path(__file__).parent.parent / "knowledge" / "subsidies.yaml"
    with open(kb_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data.get("subsidies", [])


@tool("search_subsidies")
def search_subsidies(query: str) -> str:
    """Search the subsidy knowledge base for grants matching the query.

    Use this to find subsidies that match a company's industry, size,
    or investment plans. Returns matching subsidy details including
    requirements, amounts, and scoring criteria.

    Args:
        query: Search query (industry, company size, challenge, etc.)
    """
    subsidies = _load_subsidies()
    results: list[str] = []

    query_lower = query.lower()
    for sub in subsidies:
        # Simple keyword matching (production: replace with Azure AI Search)
        searchable = " ".join([
            sub.get("name", ""),
            sub.get("purpose", ""),
            sub.get("target", ""),
            " ".join(sub.get("requirements", [])),
            " ".join(sub.get("tips", [])),
        ]).lower()

        if any(word in searchable for word in query_lower.split()):
            entry = (
                f"## {sub['name']}\\n"
                f"- 補助上限: {sub.get('max_amount', 'N/A')}\\n"
                f"- 補助率: {sub.get('subsidy_rate', 'N/A')}\\n"
                f"- 採択率: {sub.get('acceptance_rate', 'N/A')}\\n"
                f"- 対象: {sub.get('target', 'N/A')}\\n"
                f"- 目的: {sub.get('purpose', 'N/A')}\\n"
                f"- 要件: {', '.join(sub.get('requirements', []))}\\n"
            )
            if sub.get("scoring_criteria"):
                entry += f"- 審査基準: {', '.join(sub['scoring_criteria'])}\\n"
            if sub.get("tips"):
                entry += f"- Tips: {', '.join(sub['tips'])}\\n"
            results.append(entry)

    if results:
        return "\\n---\\n".join(results[:5])
    return f"該当する補助金が見つかりませんでした: {query}"


@tool("list_all_subsidies")
def list_all_subsidies() -> str:
    """List all available subsidies in the knowledge base.

    Returns a summary table of all subsidies with name, max amount, and rate.
    """
    subsidies = _load_subsidies()
    header = "| 補助金名 | 補助上限額 | 補助率 | 採択率 |"
    sep = "|---------|----------|-------|--------|"
    lines = [header, sep]
    for sub in subsidies:
        lines.append(
            f"| {sub.get('short_name', sub['name'])} "
            f"| {sub.get('max_amount', 'N/A')} "
            f"| {sub.get('subsidy_rate', 'N/A')} "
            f"| {sub.get('acceptance_rate', 'N/A')} |"
        )
    return "\\n".join(lines)
