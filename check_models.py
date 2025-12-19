import google.generativeai as genai
from config import settings

# =================================================================
# 利用可能な Gemini モデルの一覧を確認するスクリプト
# config.py の settings 経由で環境変数を取得します
# =================================================================

api_key = settings.GEMINI_API_KEY

if not api_key:
    print("エラー: 環境変数 'GEMINI_API_KEY' が設定されていません。")
else:
    # IPv4強制パッチ (一部の環境での名前解決エラー対策)
    import socket
    _original_getaddrinfo = socket.getaddrinfo
    def _ipv4_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
        if family == socket.AF_UNSPEC:
            family = socket.AF_INET
        return _original_getaddrinfo(host, port, family, type, proto, flags)
    socket.getaddrinfo = _ipv4_getaddrinfo

    print(f"APIキー: {api_key[:5]}... (config経由での読み込み成功)")
    print("利用可能なモデルを問い合わせ中...")
    
    genai.configure(api_key=api_key)
    
    try:
        found_any = False
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(f"- {m.name}")
                found_any = True
        
        if not found_any:
            print("利用可能なモデルが見つかりませんでした。")
            
    except Exception as e:
        print(f"エラーが発生しました: {e}")