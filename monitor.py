import urllib.request
import json
import re
from playwright.sync_api import sync_playwright

# あなた専用のDiscord Webhook URL
WEBHOOK_URL = "https://discord.com/api/webhooks/1527934212068474910/WmMe2c03qd64N2_cTVv1tdSgood1knl6odwgnMpPDlS43FDtlS6_Od9XSh_24SKjFSBR"
# コーシャハイム西馬込のダイレクト検索URL（アクセス解析ノイズ除去版）
TARGET_URL = "https://jhomes.to-kousya.or.jp/search/jkknet/service/akiyaJyokenDirect?sen_flg=1&jutaku_name=30B330FC30B730E330CF30A430E030CB30B730DE30B430E1"

def send_discord_notification(message):
    """Discordへプッシュ通知を送信する関数"""
    data = {"content": message}
    headers = {'Content-Type': 'application/json'}
    req = urllib.request.Request(WEBHOOK_URL, json.dumps(data).encode(), headers)
    try:
        urllib.request.urlopen(req)
    except Exception as e:
        print(f"通知送信エラー: {e}")

def check_jkk():
    with sync_playwright() as p:
        print("JKK監視システム起動...")
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            # JKKのサイトへアクセス
            page.goto(TARGET_URL, timeout=30000)
            page.wait_for_timeout(3000) # JavaScriptによるテーブル描画待機
            
            # ページ内の全テキストを取得
            text_content = page.locator("body").inner_text()
            
            # 「空室なし」の判定
            if "該当するデータがありません" in text_content or "検索結果：0件" in text_content:
                print("現在、空室はありません。（異常なし）")
                return
            
            # 空室リストが存在する場合、面積（㎡）を抽出して判定
            areas = re.findall(r'(\d{2,3}(?:\.\d+)?)\s*㎡', text_content)
            target_found = False
            found_areas = []
            
            for area_str in areas:
                area_val = float(area_str)
                found_areas.append(area_val)
                if area_val >= 54.0:
                    target_found = True
            
            # 54平米以上の部屋を発見した場合
            if target_found:
                msg = f"🚨 **【緊急出動】コーシャハイム西馬込 54㎡以上の空室がシステムに投下されました！**\nライバルにキープされる前に、今すぐ以下のリンクから申込ボタンを押してください！\n{TARGET_URL}"
                send_discord_notification(msg)
                print("【警告】54㎡以上の空室を発見し、Discordへ緊急通知を送信しました。")
            
            # 面積の読み取りに失敗したが、部屋は存在する場合（False Negative防止）
            elif not areas:
                msg = f"⚠️ **【注意】コーシャハイム西馬込に空室の気配があります（面積判定不能）**\n念のため、手動で確認してください。\n{TARGET_URL}"
                send_discord_notification(msg)
                print("空室らしきものを検知しましたが、面積が判定できませんでした。")
            
            # 54平米未満の部屋しかない場合
            else:
                print(f"空室はありますが、条件（54㎡以上）を満たしていません。検出面積: {found_areas}")

        except Exception as e:
            print(f"システムエラー発生: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    check_jkk()
