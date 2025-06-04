# Policy PR Check & Analysis Toolset

このリポジトリには、GitHubリポジトリのプルリクエスト(PR)情報を取得し、マニフェストドキュメントを処理・評価するための一連のPythonスクリプトが含まれています。

## スクリプト一覧と概要

1.  `get_policy_pr.py`: 指定されたGitHubリポジトリから全てのプルリクエスト情報を取得し、JSONファイルとして保存します。
2.  `merge_md_files.py`: 指定されたディレクトリ内の全てのMarkdownファイルを一つのファイルに統合します。
3.  `evaluate_proposals.py`: 統合されたマニフェストとPR情報（JSON）を基に、OpenAI APIを利用して各PR提案を評価し、結果をCSVファイルに出力します。

## セットアップ

1.  **Python環境**: スクリプトの実行にはPython 3が必要です。
2.  **必要なライブラリのインストール**:
    ```bash
    pip install requests tqdm openai
    ```
3.  **GitHub Personal Access Token**: `get_policy_pr.py` を使用するには、GitHub APIにアクセスするためのPersonal Access Tokenが必要です。
    *   `cert/github.txt` というファイルを作成し、そのファイル内にご自身のGitHub Personal Access Tokenを記述してください。
    *   **注意**: このトークンファイルはGitリポジトリにコミットしないでください。`.gitignore` に `cert/` を追加することを推奨します。
4.  **OpenAI API Key**: `evaluate_proposals.py` を使用するには、OpenAI APIキーが必要です。
    *   環境変数 `OPENAI_API_KEY` にご自身のAPIキーを設定してください。
    ```bash
    export OPENAI_API_KEY="sk-YourActualOpenAIKey"
    ```
    (上記は一例です。お使いのシェルに合わせて環境変数を設定してください。シェルの設定ファイル (`.bashrc`, `.zshrc` など) に追記すると永続化できます。)

## スクリプトの使い方

### 1. `get_policy_pr.py`

このスクリプトは、GitHubリポジトリからプルリクエストの情報を取得します。

**設定箇所:**
スクリプト内の以下の定数を必要に応じて変更してください。
*   `OWNER`: リポジトリのオーナー名 (デフォルト: `"team-mirai"`)
*   `REPO`: リポジトリ名 (デフォルト: `"policy"`)
*   `get_github_token()` 関数の `file_path`: トークンファイルのパス (デフォルト: `"cert/github.txt"`)

**実行方法:**
```bash
python get_policy_pr.py
```

**出力:**
*   `pull_requests_summary.json`: 取得したPR情報（番号、タイトル、ユーザー、状態、作成日時、マージ日時、本文）がJSON形式で保存されます。

### 2. `merge_md_files.py`

このスクリプトは、指定されたディレクトリ内の全てのMarkdown (`.md`) ファイルを結合し、一つのMarkdownファイルとして出力します。

**設定箇所:**
スクリプト内の以下の変数を必要に応じて変更してください。
*   `policy_dir`: 結合対象のMarkdownファイルが含まれるディレクトリのパス (デフォルト: `"libs/policy/"`)
*   `output_filename`: 出力される結合後ファイル名 (デフォルト: `"merged_policies.md"`)

**実行方法:**
```bash
python merge_md_files.py
```

**出力:**
*   `merged_policies.md` (または指定した出力ファイル名): `policy_dir` 内の全Markdownファイルの内容が、ファイル名ごとの区切りヘッダーと共に結合されて保存されます。

### 3. `evaluate_proposals.py`

このスクリプトは、`merge_md_files.py` で生成されたマニフェストファイルと `get_policy_pr.py` で生成されたPR情報JSONを読み込み、OpenAIの `gpt-4o-mini` モデルを使用して各PR提案を指定された観点から評価します。

**前提条件:**
*   `merged_policies.md` (マニフェストファイル) が存在すること。
*   `pull_requests_summary.json` (PR情報ファイル) が存在すること。
*   環境変数 `OPENAI_API_KEY` が設定されていること。

**設定箇所:**
スクリプト内の以下の定数を必要に応じて変更してください。
*   `MANIFEST_FILE`: マニフェストファイル名 (デフォルト: `"merged_policies.md"`)
*   `PROPOSALS_FILE`: PR情報ファイル名 (デフォルト: `"pull_requests_summary.json"`)
*   `OUTPUT_CSV_FILE`: 評価結果を出力するCSVファイル名 (デフォルト: `"evaluated_proposals.csv"`)
*   `GPT_MODEL`: 使用するGPTモデル (デフォルト: `"gpt-4o-mini"`)

**実行方法:**
```bash
python evaluate_proposals.py
```

**出力:**
*   `evaluated_proposals.csv`: 各PR提案について、以下の情報がCSV形式で保存されます。
    *   PR番号
    *   タイトル
    *   実現性スコア (0-10)
    *   インパクトスコア (0-10)
    *   政策整合性スコア (0-10)
    *   透明性スコア (0-10)
    *   ROIスコア (0-10)
    *   考察 (LLMによる評価根拠、日本語約400字)

## ワークフロー例

1.  `cert/github.txt` にGitHubトークンを設定します。
2.  `python get_policy_pr.py` を実行して、`pull_requests_summary.json` を生成します。
3.  マニフェストのMarkdownファイル群を `libs/policy/` (またはスクリプトで指定したディレクトリ) に配置します。
4.  `python merge_md_files.py` を実行して、`merged_policies.md` を生成します。
5.  環境変数 `OPENAI_API_KEY` を設定します。
6.  `python evaluate_proposals.py` を実行して、`evaluated_proposals.csv` を生成します。

## 注意事項

*   各スクリプトのファイルパス設定は、スクリプトがプロジェクトのルートディレクトリから実行されることを想定しています。異なる場所から実行する場合は、パスを適宜調整してください。
*   OpenAI APIの利用にはコストが発生する場合があります。利用状況にご注意ください。
*   GitHub Personal Access Token および OpenAI API Key は機密情報です。これらの情報が誤ってリポジトリにコミットされたり、公開されたりしないように厳重に管理してください。 