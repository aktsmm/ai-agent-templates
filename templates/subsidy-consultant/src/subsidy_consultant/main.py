"""Subsidy Consultant - CLI Entry Point.

Usage:
    # マッチング: 企業情報から最適な補助金を検索
    python -m subsidy_consultant match \\
        --industry 製造業 --employees 30 \\
        --capital 3000万円 --location 東京都 \\
        --challenge "生産ラインの自動化"

    # 申請書ドラフト生成
    python -m subsidy_consultant draft \\
        --subsidy ものづくり補助金 \\
        --company "製造業、従業員30名" \\
        --plan "AI外観検査装置の導入"

    # 申請書スコアリング
    python -m subsidy_consultant score \\
        --subsidy ものづくり補助金 --file draft.txt

    # 公募要領の要約
    python -m subsidy_consultant summarize --file guidelines.txt

    # 対話モード
    python -m subsidy_consultant
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from dotenv import load_dotenv


def main() -> None:
    """Run the subsidy consultant agent."""
    env_path = Path(__file__).parent.parent.parent / ".env"
    load_dotenv(env_path)

    parser = argparse.ArgumentParser(
        description="AI 補助金コンサルタント - Azure AI Foundry 搭載"
    )
    subparsers = parser.add_subparsers(dest="command")

    # match コマンド
    match_parser = subparsers.add_parser("match", help="補助金マッチング")
    match_parser.add_argument("--industry", "-i", required=True, help="業種")
    match_parser.add_argument("--employees", "-e", type=int, required=True, help="従業員数")
    match_parser.add_argument("--capital", "-c", required=True, help="資本金")
    match_parser.add_argument("--location", "-l", required=True, help="所在地")
    match_parser.add_argument("--challenge", required=True, help="課題・投資計画")

    # draft コマンド
    draft_parser = subparsers.add_parser("draft", help="申請書ドラフト生成")
    draft_parser.add_argument("--subsidy", "-s", required=True, help="補助金名")
    draft_parser.add_argument("--company", required=True, help="企業情報")
    draft_parser.add_argument("--plan", required=True, help="事業計画概要")
    draft_parser.add_argument("--output", "-o", help="出力ファイルパス")

    # score コマンド
    score_parser = subparsers.add_parser("score", help="申請書スコアリング")
    score_parser.add_argument("--subsidy", "-s", required=True, help="補助金名")
    score_parser.add_argument("--file", "-f", required=True, help="申請書ファイルパス")

    # summarize コマンド
    sum_parser = subparsers.add_parser("summarize", help="公募要領の要約")
    sum_parser.add_argument("--file", "-f", required=True, help="公募要領ファイルパス")

    args = parser.parse_args()

    if args.command == "match":
        _cmd_match(args)
    elif args.command == "draft":
        _cmd_draft(args)
    elif args.command == "score":
        _cmd_score(args)
    elif args.command == "summarize":
        _cmd_summarize(args)
    else:
        _interactive_mode()


def _cmd_match(args) -> None:
    from subsidy_consultant.crew import match_subsidies

    print("補助金マッチング中...")
    result = match_subsidies(
        industry=args.industry,
        employees=args.employees,
        capital=args.capital,
        location=args.location,
        challenge=args.challenge,
    )
    print(f"\n企業情報: {result.company_info}")
    print(f"\n{result.recommendations}")


def _cmd_draft(args) -> None:
    from subsidy_consultant.crew import draft_application

    print(f"申請書ドラフト生成中... ({args.subsidy})")
    result = draft_application(
        subsidy_name=args.subsidy,
        company_info=args.company,
        plan_summary=args.plan,
    )
    print(f"\n{result.draft}")

    if args.output:
        Path(args.output).write_text(result.draft, encoding="utf-8")
        print(f"\n保存先: {args.output}")


def _cmd_score(args) -> None:
    from subsidy_consultant.crew import score_application

    filepath = Path(args.file)
    if not filepath.exists():
        print(f"Error: ファイルが見つかりません: {filepath}")
        sys.exit(1)

    text = filepath.read_text(encoding="utf-8")
    print(f"申請書スコアリング中... ({args.subsidy})")
    result = score_application(subsidy_name=args.subsidy, application_text=text)
    print(f"\n{result.score_report}")


def _cmd_summarize(args) -> None:
    from subsidy_consultant.crew import summarize_guidelines

    filepath = Path(args.file)
    if not filepath.exists():
        print(f"Error: ファイルが見つかりません: {filepath}")
        sys.exit(1)

    text = filepath.read_text(encoding="utf-8")
    print("公募要領を解析中...")
    result = summarize_guidelines(guidelines_text=text)
    print(f"\n{result.summary}")


def _interactive_mode() -> None:
    from subsidy_consultant.crew import match_subsidies

    print("=" * 60)
    print("  AI 補助金コンサルタント")
    print("  Azure AI Foundry 搭載")
    print("=" * 60)
    print()

    industry = input("業種を入力してください（例: 製造業）: ").strip()
    employees = int(input("従業員数: ").strip())
    capital = input("資本金（例: 3,000万円）: ").strip()
    location = input("所在地（例: 東京都）: ").strip()
    challenge = input("課題・投資計画を教えてください: ").strip()

    print("\n補助金マッチング中...")
    result = match_subsidies(
        industry=industry,
        employees=employees,
        capital=capital,
        location=location,
        challenge=challenge,
    )
    print(f"\n{result.recommendations}")

    # 続けてドラフト生成するか確認
    print("\n" + "-" * 40)
    cont = input("申請書のドラフトを生成しますか？ (y/n): ").strip().lower()
    if cont == "y":
        from subsidy_consultant.crew import draft_application

        subsidy_name = input("補助金名: ").strip()
        plan = input("事業計画の概要: ").strip()

        company_info = f"{industry} / {employees}人 / {capital} / {location}"
        result = draft_application(
            subsidy_name=subsidy_name,
            company_info=company_info,
            plan_summary=plan,
        )
        print(f"\n{result.draft}")


if __name__ == "__main__":
    main()
