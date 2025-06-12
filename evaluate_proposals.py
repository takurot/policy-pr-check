import json
import csv
import os
import openai # OpenAIライブラリのインポートを有効化

# --- お客様による設定箇所 ---
# APIキーをファイルから読み込む関数
def get_openai_api_key(file_path="cert/openai.txt"):
    try:
        with open(file_path, 'r') as f:
            key = f.read().strip()
        if not key:
            raise ValueError("OpenAI API Key file is empty.")
        return key
    except FileNotFoundError:
        print(f"エラー: OpenAI APIキーファイルが見つかりません: {os.path.abspath(file_path)}")
        print("スクリプトを続行できません。APIキーファイルを作成し、適切な場所に配置してください。")
        exit(1)
    except ValueError as ve:
        print(f"エラー: {ve}")
        exit(1)
    except Exception as e:
        print(f"エラー: OpenAI APIキーファイルの読み込み中に予期せぬエラーが発生しました: {e}")
        exit(1)

OPENAI_API_KEY = get_openai_api_key()
MANIFEST_FILE = "merged_policies.md"
PROPOSALS_FILE = "pull_requests_summary.json"
OUTPUT_CSV_FILE = "evaluated_proposals.csv"
GPT_MODEL = "chatgpt-4o-latest" # ご指定のモデル

# OpenAIクライアントの初期化 (APIキーは環境変数から自動的に読み込まれることを期待)
# client = openai.OpenAI() # main関数内でAPIキーチェック後に初期化するように変更

# --- OpenAI API 呼び出し関数 ---
def evaluate_proposal_with_llm(client, manifest_content, proposal_title, proposal_body):
    """
    OpenAIのAPIを呼び出して、提案を評価する。
    """
    system_prompt = """
あなたは、経験豊富な政策評価アナリストです。
提示されたマニフェスト（基本政策）と個別の政策提案を比較し、厳格かつ批判的な視点で評価を行ってください。
評価の際は、各評価基準の定義をよく読み、表面的な言葉だけでなく、その背景にある実現性や影響を深く考察してください。
スコアは1から10までの整数で、安易に平均点（5-7点）に偏らないように、メリット・デメリットを明確にした上で、大胆に点数をつけてください。
最終的なアウトプTットは、指定されたJSON形式のみとしてください。その他のテキストは一切含めないでください。
"""

    prompt = f"""
# マニフェスト（基本政策）
```markdown
{manifest_content}
```

# 評価対象の政策提案
## タイトル
{proposal_title}

## 内容
{proposal_body}

---

# 評価タスク
上記の「マニフェスト」と「政策提案」を基に、以下の5つの基準で提案を評価し、結果をJSON形式で出力してください。

## 評価基準
1.  **技術的・財政的・法的な実現可能性 (feasibility_score)**:
    提案されている政策が、現在の技術、予算、法制度の枠組みの中で、どの程度現実的に実行可能か。具体的な障壁や、それを乗り越えるための前提条件も考慮して10段階で評価してください。
2.  **社会的・経済的インパクト (impact_score)**:
    この政策が実現した場合、社会や経済にどのような好影響をもたらすか。受益者は誰で、どのくらいの規模の影響が期待できるか。短期的な効果と長期的な効果を区別して10段階で評価してください。
3.  **マニフェストとの整合性 (policy_alignment_score)**:
    提示されたマニフェスト（基本政策）と、提案内容がどれだけ一致しているか。特に、マニフェストのどの項目と関連が深く、その理念を補強するものになっているか、あるいは矛盾する点はないかを10段階で評価してください。
4.  **プロセスの透明性と説明責任 (transparency_score)**:
    政策の実行プロセスや効果測定の方法が、市民に対してどれだけ透明性が高く、説明責任を果たせる設計になっているか。意思決定プロセスは明確か、効果を測るための客観的な指標は含まれているかを10段階で評価してください。
5.  **費用対効果とリスク (roi_score)**:
    投じられるリソース（予算、人員など）に対して、得られるリターン（社会的便益、経済効果など）はどの程度見込めるか。また、想定されるリスクや負の副作用も考慮し、総合的な費用対効果を10段階で評価してください。

## 総合評価と根拠 (rationale)
上記5つの評価を踏まえ、この提案の総合的な評価と、その結論に至った理由を日本語400字程度で簡潔に記述してください。

## 出力形式
以下のキーを持つJSONオブジェクトとしてください。
- feasibility_score: 整数値 (1-10)
- impact_score: 整数値 (1-10)
- policy_alignment_score: 整数値 (1-10)
- transparency_score: 整数値 (1-10)
- roi_score: 整数値 (1-10)
- rationale: 文字列

"""
    try:
        response = client.chat.completions.create(
            model=GPT_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.5, # 評価の一貫性を保つため、少し低めに設定
            max_tokens=1500,
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"エラー: '{proposal_title}' の評価中にOpenAI API呼び出しでエラーが発生しました: {e}")
        return {
            "feasibility_score": "APIエラー", "impact_score": "APIエラー",
            "policy_alignment_score": "APIエラー", "transparency_score": "APIエラー",
            "roi_score": "APIエラー", "rationale": f"OpenAI APIエラー: {e}"
        }

def main():
    # APIキーのチェックはget_openai_api_key関数内で行われるため、ここでのチェックは不要
    print(f"OpenAI APIキーがファイルから読み込まれました。")

    client = openai.OpenAI(api_key=OPENAI_API_KEY) # ファイルから読み込んだキーを使用してクライアントを初期化

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