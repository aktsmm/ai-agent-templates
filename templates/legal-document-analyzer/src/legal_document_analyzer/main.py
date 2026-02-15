"""Legal Document Analyzer Agent - Entry Point.

Usage:
    # Interactive mode (default)
    python -m legal_document_analyzer

    # Single query mode
    python -m legal_document_analyzer --query "Summarize the NDA"

    # Batch mode from file
    python -m legal_document_analyzer --file queries.txt
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from dotenv import load_dotenv


def main() -> None:
    """Run the legal document analyzer agent."""
    # Load environment variables
    env_path = Path(__file__).parent.parent.parent / ".env"
    load_dotenv(env_path)

    parser = argparse.ArgumentParser(
        description="AI Legal Document Analyzer Agent powered by CrewAI"
    )
    parser.add_argument(
        "--query", "-q",
        type=str,
        help="Single document analysis request to process",
    )
    parser.add_argument(
        "--file", "-f",
        type=str,
        help="File containing queries (one per line)",
    )
    parser.add_argument(
        "--classify-only", "-c",
        action="store_true",
        help="Only classify the request without generating a full analysis",
    )
    args = parser.parse_args()

    if args.query:
        # Single query mode
        _process_query(args.query, args.classify_only)

    elif args.file:
        # Batch mode
        filepath = Path(args.file)
        if not filepath.exists():
            print(f"Error: File not found: {filepath}")
            sys.exit(1)

        queries = filepath.read_text(encoding="utf-8").strip().splitlines()
        for i, query in enumerate(queries, 1):
            query = query.strip()
            if query and not query.startswith("#"):
                print(f"\n{'='*60}")
                print(f"Query {i}/{len(queries)}")
                print(f"{'='*60}")
                _process_query(query, args.classify_only)

    else:
        # Interactive mode
        print("=" * 60)
        print("  AI Legal Document Analyzer")
        print("  Type 'quit' or 'exit' to stop")
        print("=" * 60)

        while True:
            print()
            query = input("Query > ").strip()
            if query.lower() in ("quit", "exit", "q"):
                print("Goodbye!")
                break
            if not query:
                continue
            _process_query(query, args.classify_only)


def _process_query(query: str, classify_only: bool = False) -> None:
    """Process a single document analysis query."""
    from legal_document_analyzer.crew import analyze_document, classify_request

    print(f"\nProcessing: {query}")
    print("-" * 40)

    if classify_only:
        category = classify_request(query)
        print(f"Category: {category}")
    else:
        result = analyze_document(query)
        print(f"Category: {result.category}")
        print(f"\nAnalysis:\n{result.response}")


if __name__ == "__main__":
    main()
