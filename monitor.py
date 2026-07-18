import os
import json
import urllib.request
from playwright.sync_api import sync_playwright

# GitHubの金庫からURLを取り出す
WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

def send_discord_notification(message):
    if not WEBHOOK_URL:
        print("Webhook URLが設定されていません。")
        return
    headers = {'Content-Type': 'application/json'}
    data = json.dumps({"content": message}).encode("utf-8")
    req = urllib.request.Request(WEBHOOK_URL, data=data, headers=headers, method="POST")
    try:
        urllib.request.urlopen(req)
    except Exception as e:
        print(f"Discord通知エラー: {e}")

def check_jkk():
    send_discord_notification("🚀 JKK監視システム：Discordへの通信テストを開始します。")
    with sync_playwright() as p:
        print("ブラウザを起動中...")
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        target_url = "https://www.to-kousya.or.jp/"
        print(f"JKKサイトにアクセス中: {target_url}")
        
        try:
            response = page.goto(target_url, timeout=30000)
            print(f"ステータスコード: {response.status}")
            
            if response.status == 403:
                msg = "🚨 【失敗】GitHubのIPがJKKのセキュリティに弾かれました（403 Forbidden）"
                print(msg)
                send_discord_notification(msg)
            elif response.status == 200:
                msg = "✅ 【成功】JKKサイトへのアクセスを突破しました！監視ロジックを続行できます。"
                print(msg)
                send_discord_notification(msg)
            else:
                msg = f"⚠️ 【不明】想定外のステータスです: {response.status}"
                print(msg)
                send_discord_notification(msg)
                
        except Exception as e:
            error_msg = f"❌ エラーが発生しました: {e}"
            print(error_msg)
            send_discord_notification(error_msg)
        finally:
            browser.close()

if __name__ == "__main__":
    check_jkk()
