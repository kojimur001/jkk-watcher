import os
import json
import urllib.request
from playwright.sync_api import sync_playwright

WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
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
    # 教えていただいた正しい直リンクURL（トラッキングパラメータを除外）
    target_url = "https://jhomes.to-kousya.or.jp/search/jkknet/service/akiyaJyokenDirect?sen_flg=1&jutaku_name=30B330FC30B730E330CF30A430E030CB30B730DE30B430E1"
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            print(f"JKKサイトへアクセス中: {target_url}")
            page.goto(target_url, timeout=60000)
            
            # 【重要】ご指摘の「自動遷移」が完了するまで8秒間待機する
            print("画面の自動遷移を待機しています...")
            page.wait_for_timeout(8000)
            print(f"遷移後のURL: {page.url}")
            
            # ページ内のすべての文字を取得
            page_text = page.inner_text("body")
            
            # 空室がないときの特有のメッセージが含まれていないかチェック
            is_empty_msg = "該当するあき家はありません" in page_text or "該当する物件はありません" in page_text or "該当する住宅はありません" in page_text
            
            # 空室なしメッセージがない ＆ コーシャハイム西馬込の文字がある ＝ 空室あり！
            is_vacant_now = not is_empty_msg and "コーシャハイム西馬込" in page_text
            
            prev_state = False
            if os.path.exists(STATE_FILE):
                try:
                    with open(STATE_FILE, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        prev_state = data.get("is_vacant", False)
                except Exception:
                    pass
            
            if is_vacant_now and not prev_state:
                msg = (
                    "🚨 【JKK空室速報】コーシャハイム西馬込が出ました！🚨\n"
                    "即確認してください！\n"
                    f"🔗 {target_url}"
                )
                send_discord_notification(msg)
                print("【発見】空室を検知し、Discordへ通知しました。")
                
            elif is_vacant_now and prev_state:
                print("空室は継続中ですが、既に通知済みのためスキップします。")
                
            elif not is_vacant_now and prev_state:
                print("空室が埋まりました。監視状態をリセットします。")
                
            else:
                print("現在、コーシャハイム西馬込の空室はありません。監視を継続します。")
            
            with open(STATE_FILE, "w", encoding="utf-8") as f:
                json.dump({"is_vacant": is_vacant_now}, f)
                
        except Exception as e:
            print(f"監視中にエラーが発生しました: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    check_jkk()
