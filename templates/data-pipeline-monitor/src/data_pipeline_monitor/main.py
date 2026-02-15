"""Data Pipeline Monitor — Entry Point.

Usage:
    # Interactive mode (default)
    python -m data_pipeline_monitor

    # Single query mode
    python -m data_pipeline_monitor --query "ETL-003 failed with connection error"

    # Batch mode from file
    python -m data_pipeline_monitor --file requests.txt
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from dotenv import load_dotenv


def main() -> None:
    """Run the data pipeline monitor agent."""
    # Load environment variables
    env_path = Path(__file__).parent.parent.parent / ".env"
    load_dotenv(env_path)

    parser = argparse.ArgumentParser(
        description="AI Data Pipeline Monitor powered by CrewAI"
    )
    parser.add_argument(
        "--query", "-q",
        type=str,
        help="Single pipeline monitoring request to process",
    )
    parser.add_argument(
        "--file", "-f",
        type=str,
        help="File containing requests (one per line)",
    )
    parser.add_argument(
        "--classify-only", "-c",
        action="store_true",
        help="Only classify the request without generating a response",
    )
    args = parser.parse_args()

    if args.query:
        # Single query mode
        _process_request(args.query, args.classify_only)

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
                print(f"Request {i}/{len(queries)}")
                print(f"{'='*60}")
                _process_request(query, args.classify_only)

    else:
        # Interactive mode
        print("=" * 60)
        print("  AI Data Pipeline Monitor")
        print("  Type 'quit' or 'exit' to stop")
        print("=" * 60)

        while True:
            print()
            query = input("Operator > ").strip()
            if query.lower() in ("quit", "exit", "q"):
                print("Goodbye!")
                break
            if not query:
                continue
            _process_request(query, args.classify_only)


def _process_request(query: str, classify_only: bool = False) -> None:
    """Process a single pipeline monitoring request."""
    from data_pipeline_monitor.crew import classify_request, handle_request

    print(f"\nProcessing: {query}")
    print("-" * 40)

    if classify_only:
        category = classify_request(query)
        print(f"Category: {category}")
    else:
        result = handle_request(query)
        print(f"Category: {result.category}")
        print(f"\nResponse:\n{result.response}")


if __name__ == "__main__":
    main()
