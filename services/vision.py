import base64
import io
import socket
import logging
from PIL import Image
from fastapi import HTTPException
import google.generativeai as genai
from google.api_core import exceptions as google_exceptions
from config import settings

# --- IPv4強制パッチ (Windows環境での名前解決エラー対策) ---
# 一部の環境でIPv6アドレスの名前解決に失敗し、Gemini APIに接続できない問題を回避します。
_original_getaddrinfo = socket.getaddrinfo

def _ipv4_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
    # アドレスファミリが指定されていない場合、強制的にIPv4 (AF_INET) を使用
    if family == socket.AF_UNSPEC:
        family = socket.AF_INET
    return _original_getaddrinfo(host, port, family, type, proto, flags)

socket.getaddrinfo = _ipv4_getaddrinfo
# -------------------------------------------------------

# =================================================================
# Gemini Vision API 連携関数（旧 VisionService クラスを関数化）
# =================================================================

def get_model_name() -> list[str]:
    """現在設定されているGeminiモデル名を返します。"""
    if settings.GEMINI_MODEL:
        return [settings.GEMINI_MODEL]
    return []

def extract_text_from_image(file_bytes: bytes) -> str:
    """画像バイトを受け取り、Google Generative AI SDK (Gemini) を使用してテキストを抽出します。"""

    # APIキーの設定確認
    if not settings.GEMINI_API_KEY:
        # セキュリティのため、キーの中身はログに出さない
        raise HTTPException(
            status_code=500,
            detail="Gemini APIキーが設定されていません。.envファイルを確認してください。",
        )

    try:
        # SDKの設定
        genai.configure(api_key=settings.GEMINI_API_KEY)
        
        # 画像データの準備
        try:
            img = Image.open(io.BytesIO(file_bytes))
        except Exception:
            raise HTTPException(status_code=400, detail="無効な画像ファイルです。")

        # モデルの初期化
        model = genai.GenerativeModel(settings.GEMINI_MODEL)

        # プロンプトの作成
        prompt = "これはレシートの画像です。書かれている日本語のテキストを、改行を維持したまま全て正確に抽出してください。"

        # 生成リクエスト
        # SDKは画像オブジェクト(PIL)を直接扱えます
        response = model.generate_content([prompt, img])
        
        # レスポンスの検証とテキスト抽出
        if not response.text:
             raise HTTPException(status_code=500, detail="Gemini APIからテキストが返されませんでした。")

        return response.text.strip()

    except google_exceptions.GoogleAPICallError as e:
        # Google API固有のエラーハンドリング
        error_msg = f"Gemini API呼び出しエラー: {e.message if hasattr(e, 'message') else str(e)}"
        logging.error(error_msg)
        raise HTTPException(status_code=503, detail="Gemini APIサービスでエラーが発生しました。しばらく待って再試行してください。")
        
    except ConnectionError as e:
         logging.error(f"Network Connection Error: {e}")
         raise HTTPException(status_code=503, detail="Gemini APIへのネットワーク接続に失敗しました。")
         
    except Exception as e:
        # 予期せぬエラー
        logging.error(f"Unexpected error in image extraction: {e}")
        raise HTTPException(status_code=500, detail="画像解析中に予期せぬエラーが発生しました。")