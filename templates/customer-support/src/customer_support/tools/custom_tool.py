"""Custom tools for the customer support agent."""

from crewai.tools import tool


@tool("search_knowledge_base")
def search_knowledge_base(query: str) -> str:
    """Search the product knowledge base for relevant information.

    Use this tool to find answers to customer questions from the FAQ
    and product documentation.

    Args:
        query: The search query based on the customer's question.

    Returns:
        Relevant information from the knowledge base.
    """
    # In production, replace with vector DB search (e.g., ChromaDB, Pinecone)
    # This is a simple keyword-based fallback for the template
    from pathlib import Path

    knowledge_dir = Path(__file__).parent.parent / "knowledge"
    results: list[str] = []

    for file in knowledge_dir.glob("*.md"):
        content = file.read_text(encoding="utf-8")
        # Simple section-based search
        sections = content.split("\n## ")
        for section in sections:
            if query.lower() in section.lower():
                results.append(section.strip()[:500])

    if results:
        return "\n\n---\n\n".join(results[:3])
    return f"No relevant information found in the knowledge base for: {query}"
