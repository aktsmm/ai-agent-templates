"""E-commerce Assistant Agent - Entry Point.

Usage:
    # Interactive mode (default)
    python -m ecommerce_assistant

    # Single query mode
    python -m ecommerce_assistant --query "Do you have wireless headphones?"

    # Batch mode from file
    python -m ecommerce_assistant --file queries.txt
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from dotenv import load_dotenv


def main() -> None:
    """Run the e-commerce assistant agent."""
    # Load environment variables
    env_path = Path(__file__).parent.parent.parent / ".env"
    load_dotenv(env_path)

    parser = argparse.ArgumentParser(
        description="AI E-commerce Assistant Agent powered by CrewAI"
    )
    parser.add_argument(
        "--query", "-q",
        type=str,
        help="Single customer inquiry to process",
    )
    parser.add_argument(
        "--file", "-f",
        type=str,
        help="File containing queries (one per line)",
    )
    parser.add_argument(
        "--classify-only", "-c",
        action="store_true",
        help="Only classify the inquiry without generating a response",
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
        print("  AI E-commerce Assistant")
        print("  Type 'quit' or 'exit' to stop")
        print("=" * 60)

        while True:
            print()
            query = input("Customer > ").strip()
            if query.lower() in ("quit", "exit", "q"):
                print("Goodbye!")
                break
            if not query:
                continue
            _process_query(query, args.classify_only)


def _process_query(query: str, classify_only: bool = False) -> None:
    """Process a single customer query."""
    from ecommerce_assistant.crew import classify_inquiry, handle_inquiry

    print(f"\nProcessing: {query}")
    print("-" * 40)

    if classify_only:
        category = classify_inquiry(query)
        print(f"Category: {category}")
    else:
        result = handle_inquiry(query)
        print(f"Category: {result.category}")
        print(f"\nResponse:\n{result.response}")


if __name__ == "__main__":
    main()
