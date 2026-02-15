# 💼 補助金コンサルタント AI テンプレート

> [CrewAI](https://github.com/crewAIInc/crewAI) + [Azure AI Foundry](https://azure.microsoft.com/products/ai-foundry) で構築する、中小企業向け補助金申請支援エージェント。マッチング・申請書ドラフト・スコアリング・公募要領解析を自動化。

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![CrewAI](https://img.shields.io/badge/CrewAI-1.9%2B-green.svg)](https://github.com/crewAIInc/crewAI)
[![Azure OpenAI](https://img.shields.io/badge/Azure%20OpenAI-gpt--4o-0078D4.svg)](https://azure.microsoft.com/products/ai-services/openai-service)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-29%20passed-brightgreen.svg)](#testing)

## Features

- **4 つの専門エージェント** — マッチング・ライティング・スコアリング・要約
- **Azure AI Foundry 対応** — gpt-4o / gpt-4o-mini のデュアルモデル構成
- **YAML 設定** — コード変更なしでエージェント挙動をカスタマイズ
- **補助金ナレッジベース** — YAML 形式で補助金データを管理（拡張容易）
- **4 つの CLI コマンド** — match / draft / score / summarize + 対話モード
- **29 ユニットテスト** — モック付きテストスイート完備

## How It Works

```
企業情報入力
      |
      v
+------------------+
|  Matcher Agent   |  ← 補助金データベースから最適制度を検索
+--------+---------+
         |
   +-----+-----+------+
   |           |      |
   v           v      v
 Writer     Scorer   Summarizer
 Agent      Agent     Agent
 (ドラフト)  (採点)    (要約)
```

| Agent          | 役割                         | モデル                       |
| -------------- | ---------------------------- | ---------------------------- |
| **Matcher**    | 企業×補助金のマッチング      | gpt-4o-mini (高速・低コスト) |
| **Writer**     | 事業計画書のドラフト生成     | gpt-4o (高品質)              |
| **Scorer**     | 審査基準に基づくスコアリング | gpt-4o                       |
| **Summarizer** | 公募要領の構造化要約         | gpt-4o-mini                  |

## Quick Start

### 1. Install

```bash
# Using pip
pip install -e .

# Using uv (recommended, faster)
uv pip install -e .
```

### 2. Configure Azure OpenAI

```bash
cp .env.example .env
# Edit .env with your Azure OpenAI credentials
```

Azure OpenAI リソースの情報取得:

```bash
# リソース一覧
az cognitiveservices account list --query "[?kind=='OpenAI'].{name:name, rg:resourceGroup, endpoint:properties.endpoint}" -o table

# API キー取得
az cognitiveservices account keys list --name YOUR-RESOURCE --resource-group YOUR-RG --query key1 -o tsv

# デプロイメント一覧
az cognitiveservices account deployment list --name YOUR-RESOURCE --resource-group YOUR-RG --query "[].{name:name, model:properties.model.name}" -o table
```

### 3. Run

```bash
# 補助金マッチング
python -m subsidy_consultant match \
  --industry "IT" \
  --employees 10 \
  --capital "1,000万円" \
  --location "東京都" \
  --challenge "AI活用した業務自動化ツールの開発"

# 申請書ドラフト生成
python -m subsidy_consultant draft \
  --subsidy "ものづくり補助金" \
  --company "IT企業、従業員10名、東京都" \
  --plan "AI検査システムの開発・導入"

# 申請書スコアリング
python -m subsidy_consultant score \
  --subsidy "ものづくり補助金" \
  --file draft.txt

# 公募要領の要約
python -m subsidy_consultant summarize --file guidelines.txt

# 対話モード
python -m subsidy_consultant
```

## Customization

### 補助金データの追加

`src/subsidy_consultant/knowledge/subsidies.yaml` を編集:

```yaml
subsidies:
  - name: "新しい補助金名"
    max_amount: "500万円"
    subsidy_rate: "2/3"
    target: "中小企業"
    purpose: "DX推進"
    requirements:
      - "従業員数300人以下"
      - "資本金3億円以下"
```

### エージェント挙動の変更

YAML 設定ファイルを編集するだけ（コード変更不要）:

- `src/subsidy_consultant/config/agents.yaml` — エージェントの役割・目標・バックストーリー
- `src/subsidy_consultant/config/tasks.yaml` — タスクの説明と期待出力

## Project Structure

```
subsidy-consultant/
├── .env.example            # Azure OpenAI 設定テンプレート
├── pyproject.toml           # 依存関係 & プロジェクトメタデータ
├── README.md
├── src/
│   └── subsidy_consultant/
│       ├── main.py          # CLI エントリーポイント
│       ├── crew.py          # エージェント & タスク定義
│       ├── config/
│       │   ├── agents.yaml  # エージェント設定
│       │   └── tasks.yaml   # タスク設定
│       ├── tools/
│       │   └── subsidy_search.py  # 補助金検索ツール
│       └── knowledge/
│           └── subsidies.yaml     # 補助金データベース
└── tests/
    └── test_subsidy.py      # ユニットテスト (29件)
```

## Testing

```bash
pip install -e ".[dev]"
pytest -v
```

29 tests covering:

- 補助金ナレッジベースのデータ整合性 (3 tests)
- 検索ツールのキーワードマッチング (5 tests)
- Pydantic モデルのバリデーション (5 tests)
- Azure OpenAI LLM 設定 (3 tests)
- YAML 設定ファイルの検証 (3 tests)
- エージェント/タスクファクトリ (2 tests)
- match/draft/score 統合テスト (3 tests)
- CLI 引数パース (2 tests)
- 環境・セキュリティチェック (3 tests)

## Troubleshooting

| 問題                              | 解決策                                                    |
| --------------------------------- | --------------------------------------------------------- |
| `AZURE_OPENAI_API_KEY` が効かない | CrewAI は `AZURE_API_KEY` を使う場合あり — 両方設定を推奨 |
| `azure-ai-inference` エラー       | `pip install "crewai[azure-ai-inference]"` を実行         |
| デプロイメントが見つからない      | `az cognitiveservices account deployment list` で確認     |

## ⚠️ 免責事項

本テンプレートは **参考ツール** です。AI が生成する補助金情報・申請書ドラフトは、必ず専門家（税理士・中小企業診断士）の確認を受けてから使用してください。法的助言を提供するものではありません。

## License

MIT - See [LICENSE](LICENSE) for details.

---

Built with [CrewAI](https://github.com/crewAIInc/crewAI) + [Azure AI Foundry](https://azure.microsoft.com/products/ai-foundry)
