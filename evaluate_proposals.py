import json
import csv
import os
import openai # OpenAIライブラリのインポートを有効化

# --- お客様による設定箇所 ---
# APIキーは環境変数 OPENAI_API_KEY から読み込むことを推奨
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MANIFEST_FILE = "merged_policies.md"
PROPOSALS_FILE = "pull_requests_summary.json"
OUTPUT_CSV_FILE = "evaluated_proposals.csv"
GPT_MODEL = "gpt-4o-mini" # ご指定のモデル

# OpenAIクライアントの初期化 (APIキーは環境変数から自動的に読み込まれることを期待)
# client = openai.OpenAI() # main関数内でAPIキーチェック後に初期化するように変更

# --- OpenAI API 呼び出し関数 ---
def evaluate_proposal_with_llm(client, manifest_content, proposal_title, proposal_body):
    """
    OpenAI APIを使用して、提案をマニフェストに基づいて評価します。
    """
    # APIキーの存在は呼び出し元(main)でチェック済み想定

    prompt = f"""あなたは政策評価アシスタントです。以下の政党マニフェストと改善提案を分析し、指定された観点から評価してください。

# 政党マニフェスト
{manifest_content}

# 改善提案
## タイトル
{proposal_title}
## 内容
{proposal_body}

# 評価基準と出力形式
以下の各項目について10点満点で採点し、その評価の根拠となる考察を日本語で400字程度で記述してください。
出力は必ず以下のJSON形式でお願いします。キーの名称も完全に一致させてください。

{{
  "feasibility_score": <0-10の整数>,
  "impact_score": <0-10の整数>,
  "policy_alignment_score": <0-10の整数>,
  "transparency_score": <0-10の整数>,
  "roi_score": <0-10の整数>,
  "rationale": "<考察 (日本語400字程度)>"
}}

評価観点:
1.  実現性 (Feasibility): 提案されている政策や改善が、現在の技術的、財政的、政治的、社会的な状況を考慮した上で、実際に実行可能か。
2.  インパクト (Impact): 提案が実現した場合に、社会や対象とする分野に与える影響の大きさや範囲。正負両面を考慮。
3.  政策整合性 (Policy Alignment): 提案が、提示された政党マニフェスト全体の方向性や他の主要政策と矛盾なく、整合性が取れているか。
4.  透明性 (Transparency): 提案の意思決定プロセスや実施プロセス、効果測定の方法が、国民や関係者に対して明確で理解しやすいか。情報公開の度合い。
5.  ROI (Return on Investment): 投じられるリソース（予算、人員、時間など）に対して、得られると期待される成果や便益の度合い。費用対効果。
"""
    try:
        print(f"OpenAI APIに '{proposal_title}' の評価をリクエストします...")
        response = client.chat.completions.create(
            model=GPT_MODEL,
            messages=[
                {"role": "system", "content": "あなたは政策評価のエキスパートであり、指示されたJSON形式で正確に出力します。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3, # 安定した出力を得るために低めの温度設定
            max_tokens=1000,  # 評価と考察に十分なトークン数 (400字の考察 + JSON構造)
            response_format={"type": "json_object"}
        )
        raw_response_content = response.choices[0].message.content
        evaluation = json.loads(raw_response_content)
        print(f"'{proposal_title}' の評価をAPIから取得完了。")
        return evaluation
    except json.JSONDecodeError as json_e:
        print(f"エラー: '{proposal_title}' の評価結果のJSONパースに失敗しました: {json_e}")
        print(f"失敗したレスポンス (先頭500文字): {raw_response_content[:500] if 'raw_response_content' in locals() else 'N/A'}")
        return {
            "feasibility_score": "JSONパースエラー", "impact_score": "JSONパースエラー",
            "policy_alignment_score": "JSONパースエラー", "transparency_score": "JSONパースエラー",
            "roi_score": "JSONパースエラー", "rationale": f"JSONパースエラー: {json_e}. Raw: {raw_response_content[:200] if 'raw_response_content' in locals() else 'N/A'}..."
        }
    except Exception as e:
        print(f"エラー: '{proposal_title}' の評価中にOpenAI API呼び出しでエラーが発生しました: {e}")
        return {
            "feasibility_score": "APIエラー", "impact_score": "APIエラー",
            "policy_alignment_score": "APIエラー", "transparency_score": "APIエラー",
            "roi_score": "APIエラー", "rationale": f"OpenAI APIエラー: {e}"
        }

def main():
    if not OPENAI_API_KEY:
        print("エラー: 環境変数 OPENAI_API_KEY が設定されていません。")
        print("スクリプトを続行できません。APIキーを設定してから再実行してください。")
        return
    print(f"OpenAI APIキーが環境変数から読み込まれました。") # APIキー自体の表示は避ける

    client = openai.OpenAI() # APIキーチェック後にクライアントを初期化

    # マニフェストファイルの読み込み
    try:
        with open(MANIFEST_FILE, 'r', encoding='utf-8') as f:
            manifest_content = f.read()
        print(f"マニフェストファイル '{MANIFEST_FILE}' を読み込みました。")
    except FileNotFoundError:
        print(f"エラー: マニフェストファイルが見つかりません: {os.path.abspath(MANIFEST_FILE)}")
        return
    except Exception as e:
        print(f"エラー: マニフェストファイルの読み込み中にエラーが発生しました: {e}")
        return

    # 改善提案JSONファイルの読み込み
    try:
        with open(PROPOSALS_FILE, 'r', encoding='utf-8') as f:
            proposals_data = json.load(f)
        print(f"改善提案ファイル '{PROPOSALS_FILE}' を読み込みました。")
    except FileNotFoundError:
        print(f"エラー: 改善提案JSONファイルが見つかりません: {os.path.abspath(PROPOSALS_FILE)}")
        return
    except json.JSONDecodeError:
        print(f"エラー: {PROPOSALS_FILE} のJSON形式が正しくありません。")
        return
    except Exception as e:
        print(f"エラー: 改善提案ファイルの読み込み中にエラーが発生しました: {e}")
        return

    if not isinstance(proposals_data, list):
        print(f"エラー: {PROPOSALS_FILE} 内のデータはリスト形式である必要がありますが、{type(proposals_data)} です。")
        return

    csv_results = []
    csv_headers = [
        "PR番号", "タイトル", "実現性スコア", "インパクトスコア", "政策整合性スコア",
        "透明性スコア", "ROIスコア", "考察"
    ]
    # csv_results.append(csv_headers) # ヘッダー行はwriter.writerowで個別に追加

    print(f"{len(proposals_data)}件の改善案の評価を開始します...")
    for i, proposal in enumerate(proposals_data):
        pr_number = proposal.get("number", "N/A") # PR番号を取得
        proposal_title = proposal.get("title", f"タイトル不明な提案 {i+1}")
        proposal_body = proposal.get("body", "")

        print(f"処理中 ({i+1}/{len(proposals_data)}): PR #{pr_number} - {proposal_title}")
        
        # LLMによる評価の実行
        evaluation = evaluate_proposal_with_llm(client, manifest_content, proposal_title, proposal_body)
        
        csv_results.append([
            pr_number, # PR番号をリストの先頭に追加
            proposal_title,
            evaluation.get("feasibility_score", "N/A"),
            evaluation.get("impact_score", "N/A"),
            evaluation.get("policy_alignment_score", "N/A"),
            evaluation.get("transparency_score", "N/A"),
            evaluation.get("roi_score", "N/A"),
            evaluation.get("rationale", "N/A")
        ])
        print(f"完了 ({i+1}/{len(proposals_data)}): PR #{pr_number} - {proposal_title}")

    # CSVファイルへの書き出し
    try:
        with open(OUTPUT_CSV_FILE, 'w', newline='', encoding='utf-8-sig') as csvfile: # utf-8-sigでExcelでの文字化け防止
            writer = csv.writer(csvfile)
            writer.writerow(csv_headers) # ヘッダーを書き出し
            writer.writerows(csv_results) # データ行を書き出し
        print(f"評価結果をCSVファイルに出力しました: {os.path.abspath(OUTPUT_CSV_FILE)}")
    except Exception as e:
        print(f"エラー: CSVファイルへの書き出し中にエラーが発生しました: {e}")

if __name__ == "__main__":
    main() 