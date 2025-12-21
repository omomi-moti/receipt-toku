import io
import json
import logging
from typing import Any

from fastapi import HTTPException
from google.genai import types
from loguru import logger
from PIL import Image

from config import settings
from schemas import GeminiReceiptResponse
from model import client

from .prompt import SYSTEM_INSTRUCTION


async def analyze_receipt_with_market_data(
        file_bytes: bytes,
        market_data: list[dict[str, str | int | float]]
) -> dict[str, Any]:
    """最新の google-genai SDK を使用して詳細なAI分析を実行します。"""
    if not settings.GEMINI_API_KEY:
        logger.error("Gemini APIキーが設定されていません。")
        raise HTTPException(status_code=500, detail="Gemini APIキーが設定されていません。")

    try:
        # プロンプトの組み立て
        logger.info("Preparing prompt for Gemini analysis...")
        market_data_json = json.dumps(market_data, ensure_ascii=False, indent=2)
        full_prompt = SYSTEM_INSTRUCTION.replace("{{MARKET_DATA_JSON}}", market_data_json)
        # 画像の読み込み

        logger.info("Loading image for Gemini analysis...")
        img = Image.open(io.BytesIO(file_bytes))
        logger.info("Image loaded successfully.")

        # 構造化出力を使用してGemini APIを呼び出し
        response = await client.aio.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=[full_prompt, img],  # type: ignore
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=GeminiReceiptResponse
            )
        )
        logger.info("Gemini analysis completed.")
        if not response.text:
            logger.error("Gemini APIから有効な応答がありませんでした。")
            raise HTTPException(status_code=500, detail="Gemini APIから有効な応答がありませんでした。")

        # 構造化出力により、JSONは既に正しい形式で返される
        text = response.text.strip()
        logger.info(f"Raw Gemini response text: {text}")
        return json.loads(text)

    except Exception as e:
        logging.error(f"Gemini Analysis Error: {e}")
        raise HTTPException(status_code=500, detail=f"AI分析中にエラーが発生しました: {str(e)}")


# 互換性のための関数
def get_model_name() -> list[str]:
    return [settings.GEMINI_MODEL]
