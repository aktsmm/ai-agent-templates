"""Custom tools for the legal document analyzer agent."""

from crewai.tools import tool


@tool("search_document_clauses")
def search_document_clauses(query: str) -> str:
    """Search legal documents in the knowledge base for specific clauses or terms.

    Use this tool to find contract clauses, provisions, or legal terms
    based on keywords such as clause types, section names, or legal concepts.

    Args:
        query: The search query for finding relevant clauses or sections.

    Returns:
        Matching sections from the legal documents in the knowledge base.
    """
    from pathlib import Path

    knowledge_dir = Path(__file__).parent.parent / "knowledge"
    results: list[str] = []

    for file in sorted(knowledge_dir.glob("*.md")):
        content = file.read_text(encoding="utf-8")
        sections = content.split("\n## ")
        for section in sections:
            if query.lower() in section.lower():
                # Include the heading marker back and truncate
                entry = section.strip()[:800]
                results.append(f"[{file.stem}] {entry}")

    if results:
        return "\n\n---\n\n".join(results[:10])
    return f"No clauses or sections found matching: {query}"


@tool("get_document_sections")
def get_document_sections(document_name: str) -> str:
    """Get an overview of all sections in a legal document.

    Use this tool to see the structure and section headings of a document
    before drilling into specific clauses.

    Args:
        document_name: The name of the document to inspect (e.g., 'nda_template').

    Returns:
        A list of section headings found in the document.
    """
    from pathlib import Path

    knowledge_dir = Path(__file__).parent.parent / "knowledge"

    # Try exact match first, then partial match
    target_file = None
    for file in knowledge_dir.glob("*.md"):
        if document_name.lower() in file.stem.lower():
            target_file = file
            break

    if not target_file:
        available = [f.stem for f in knowledge_dir.glob("*.md")]
        return (
            f"Document not found: {document_name}. "
            f"Available documents: {', '.join(available) if available else 'none'}"
        )

    content = target_file.read_text(encoding="utf-8")
    headings: list[str] = []
    for line in content.splitlines():
        if line.startswith("#"):
            headings.append(line.strip())

    if headings:
        return f"Document: {target_file.stem}\n\n" + "\n".join(headings)
    return f"No section headings found in {target_file.stem}"


@tool("compare_document_sections")
def compare_document_sections(section_title: str) -> str:
    """Compare a specific section across multiple legal documents in the knowledge base.

    Use this tool when comparing how different contracts handle the same
    topic (e.g., comparing indemnification clauses across two agreements).

    Args:
        section_title: The section title or topic to compare across documents.

    Returns:
        The matching sections from each document, side by side.
    """
    from pathlib import Path

    knowledge_dir = Path(__file__).parent.parent / "knowledge"
    results: list[str] = []

    for file in sorted(knowledge_dir.glob("*.md")):
        content = file.read_text(encoding="utf-8")
        sections = content.split("\n## ")
        for section in sections:
            first_line = section.split("\n")[0].strip().lower()
            if section_title.lower() in first_line:
                entry = section.strip()[:1000]
                results.append(f"### [{file.stem}]\n{entry}")

    if results:
        return "\n\n---\n\n".join(results)
    return f"No sections titled '{section_title}' found across documents."
