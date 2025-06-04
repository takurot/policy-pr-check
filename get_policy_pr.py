import requests
import json
import time
from tqdm import tqdm
import os # osモジュールをインポート

# GitHubトークンをファイルから読み込む関数
def get_github_token(file_path="cert/github.txt"):
    try:
        with open(file_path, 'r') as f:
            token = f.read().strip()
        if not token:
            raise ValueError("Token file is empty.")
        return token
    except FileNotFoundError:
        print(f"エラー: トークンファイルが見つかりません: {os.path.abspath(file_path)}")
        print("スクリプトを続行できません。トークンファイルを作成し、適切な場所に配置してください。")
        exit(1)
    except ValueError as ve:
        print(f"エラー: {ve}")
        exit(1)
    except Exception as e:
        print(f"エラー: トークンファイルの読み込み中に予期せぬエラーが発生しました: {e}")
        exit(1)

# 認証トークンと対象リポジトリ
GITHUB_TOKEN = get_github_token()
OWNER = "team-mirai"
REPO = "policy"
HEADERS = {"Authorization": f"token {GITHUB_TOKEN}"}

def get_pull_requests():
    prs = []
    for page in tqdm(range(1, 18 + 1), desc="Fetching PR pages"):  # 1700件 / 100 = 最大18ページ
        url = f"https://api.github.com/repos/{OWNER}/{REPO}/pulls"
        params = {"state": "all", "per_page": 100, "page": page}
        res = requests.get(url, headers=HEADERS, params=params)
        data = res.json()
        if not data:
            break
        prs.extend(data)
        time.sleep(1)  # Rate limit回避
    return prs

def main():
    all_data = []
    prs = get_pull_requests()
    for pr in tqdm(prs, desc="Processing PRs"):
        pr_info = {
            "number": pr["number"],
            "title": pr["title"],
            "user": pr["user"]["login"],
            "state": pr["state"],
            "created_at": pr["created_at"],
            "merged_at": pr.get("merged_at"),
            "body": pr["body"]  # PR本文
        }
        all_data.append(pr_info)
    with open("pull_requests_summary.json", "w") as f:
        json.dump(all_data, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    main()

