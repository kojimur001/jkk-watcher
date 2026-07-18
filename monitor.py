import os
import json
import urllib.request
from playwright.sync_api import sync_playwright

WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

# 前回「空室があったか・なかったか」だけを記録するファイル
STATE_FILE = "jkk_state.json"

def send_discord_notification(message):
    if not WEBHOOK_URL:
        print("Webhook URLが設定されていません。")
        return
    headers = {
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
    }
    data = json.dumps({"content": message}).encode("utf-8")
    req = urllib.request.Request(WEBHOOK_URL, data=data, headers=headers, method="POST")
    try:
        urllib.request.urlopen(req)
    except Exception as e:
        print(f"Discord通知エラー: {e}")

def check_jkk():
    # 大田区の検索結果ページ
    target_url = "https://chintai.to-kousya.or.jp/search/result.php?ku%5B%5D=13111&sort=1&page=1"
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            print(f"JKKサイト（大田区一覧）へアクセス中: {target_url}")
            page.goto(target_url, timeout=60000)
            
            # 画面内の文字が読み込まれるまで5秒だけ待機
            page.wait_for_timeout(5000)
            
            # ページ内にある「すべての文字」をごっそり取得
            page_text = page.inner_text("body")
            
            # 「コーシャハイム西馬込」という文字が含まれているかチェック（True か False）
            is_vacant_now = "コーシャハイム西馬込" in page_text
            
            # 前回の状態を読み込む（5分ごとの連続通知スパムを防ぐため）
            prev_state = False
            if os.path.exists(STATE_FILE):
                try:
                    with open(STATE_FILE, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        prev_state = data.get("is_vacant", False)
                except Exception:
                    pass
            
            # 判定ロジック
            if is_vacant_now and not prev_state:
                # 前回は無くて、今回見つかった場合（新規出現）
                msg = (
                    "🚨 【JKK空室速報】コーシャハイム西馬込が出ました！🚨\n"
                    "大田区の検索結果に物件名が出現しました。面積・間取り問わず即確認してください！\n"
                    f"🔗 {target_url}"
                )
                send_discord_notification(msg)
                print("【発見】空室を検知し、Discordへ通知しました。")
                
            elif is_vacant_now and prev_state:
                # 前回も見つかっていて、まだ空いている場合（通知スパム防止）
                print("空室は継続中ですが、既に通知済みのためスキップします。")
                
            elif not is_vacant_now and prev_state:
                # 誰かに取られて空室が消滅した場合（状態リセット）
                print("空室が埋まりました。監視状態をリセットします。")
                
            else:
                # ずっと空室がない場合（平常運転）
                print("現在、コーシャハイム西馬込の空室はありません。監視を継続します。")
            
            # 今回の結果を保存する
            with open(STATE_FILE, "w", encoding="utf-8") as f:
                json.dump({"is_vacant": is_vacant_now}, f)
                
        except Exception as e:
            print(f"監視中にエラーが発生しました: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    check_jkk()
