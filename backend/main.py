import asyncio
from typing import Any
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from config import settings
from services import (
    EStatClient, get_model_name, analyze_receipt_with_market_data
)

app = FastAPI(title="Receipt AI Analyzer", version="2.0-advanced")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

estat_client = EStatClient()


@app.get("/health")
def health() -> dict[str, Any]:
    return {
        "ok": True,
        "vision_model": get_model_name(),
        "estat_app_id_set": bool(settings.APP_ID),
    }


@app.post("/analyzeReceipt")
async def analyze_receipt(
    file: UploadFile = File(...),
    area_code: str = "00000",
):
    """
    レシート画像をAIで高度分析します。
    1. 市場価格の最新コンテキストを準備（モックまたはAPI取得）
    2. 画像と市場価格をGeminiに送信
    3. AIによる正規化・比較結果を返却
    """
    file_bytes = await file.read()
    # 実際にはここでも非同期で e-Stat を叩いて市場価格を集めることができます
    # 今回は高度なプロンプトの威力を試すため、代表的な市場価格をコンテキストとして定義
    market_data: list[dict[str, Any]] = [
        {"item_name": "たまねぎ", "price": 418, "unit": "kg"},
        {"item_name": "にんじん", "price": 350, "unit": "kg"},
        {"item_name": "鶏卵", "price": 280, "unit": "パック(10個)"},
        {"item_name": "牛乳", "price": 250, "unit": "本(1000ml)"},
        {"item_name": "食パン", "price": 180, "unit": "袋"},
        {"item_name": "米", "price": 2500, "unit": "5kg"}
    ]

    # Gemini による高度な画像解析を実行（プログラミングによる計算ではなく、AIの推論に任せる）
    # ※ LLM呼び出しは時間がかかるため、スレッドプールで実行
    try:
        logger.info("Starting AI analysis with market data...")
        async with asyncio.TaskGroup() as tg:
            logger.info("Creating task for analyze_receipt_with_market_data...")
            task = tg.create_task(analyze_receipt_with_market_data(file_bytes, market_data))
            logger.info("Task created, awaiting result...")

        analysis_result = task.result()
        logger.info("AI analysis task completed.")

        return analysis_result

    except* Exception as eg:
        for e in eg.exceptions:
            print(f"Error during AI analysis: {str(e)}")
