from config import settings

# =================================================================
# 利用可能な Gemini モデルの一覧を確認するスクリプト (最新版)
# config.py の settings 経由で環境変数を取得します
# =================================================================

api_key = settings.GEMINI_API_KEY

if not api_key:
    print("エラー: 環境変数 'GEMINI_API_KEY' が設定されていません。")
else:
    print(f"APIキー: {api_key[:5]}... (config経由での読み込み成功)")
    print("利用可能なモデルを問い合わせ中...")

    try:
        # 最新の Client インスタンス化

        found_any = False
        # 最新のモデル一覧取得方法
        for m in api_key.models.list():
            print(f"- {m.name} (入力: {m.input_token_limit} tokens)")
            found_any = True

        if not found_any:
            print("利用可能なモデルが見つかりませんでした。")

    except Exception as e:
        print(f"エラーが発生しました: {e}")
