from playwright.sync_api import sync_playwright

def check_jkk():
    with sync_playwright() as p:
        print("ブラウザを起動中...")
        # クラウド上で動かすため画面なし(headless=True)で起動
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # JKKのサイトへアクセス（まずはアクセス制限の突破テスト）
        target_url = "https://chintai.to-kousya.or.jp/"
        
        print(f"JKKサイトにアクセス中: {target_url}")
        try:
            response = page.goto(target_url, timeout=30000)
            print(f"ステータスコード: {response.status}")
            
            if response.status == 403:
                print("【失敗】GitHubのIPがJKKのセキュリティに弾かれました（403 Forbidden）")
            elif response.status == 200:
                print("【成功】サイトへのアクセスを突破しました！監視ロジックを続行できます。")
            else:
                print(f"【不明】想定外のステータスです: {response.status}")
                
        except Exception as e:
            print(f"エラーが発生しました: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    check_jkk()
