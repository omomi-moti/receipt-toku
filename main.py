import asyncio
import re
from typing import Any, Optional

from fastapi import FastAPI, File, UploadFile, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from config import settings, ITEM_RULES
from schemas import AnalyzeResponse, ItemResult, EstatResult
from services import (
    EStatClient, get_model_name, analyze_receipt_with_market_data,
    yyyymm_from_date, resolve_time_code, resolve_area_code, judge
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
def health():
    return {
        "ok": True,
        "vision_model": get_model_name(),
        "estat_app_id_set": bool(settings.APP_ID),
    }

async def get_market_data_context(area_code: str, yyyymm: str) -> list[dict]:
    """e-Statから主要品目の市場価格リストを取得し、AIに渡すための形式に整えます。"""
    try:
        statsDataId = await estat_client.pick_stats_data_id()
        class_maps = await estat_client.get_class_maps(statsDataId)
        _, cdTime = resolve_time_code(class_maps, yyyymm)
        _, cdArea = resolve_area_code(class_maps, area_code)

        market_data = []
        # ITEM_RULESにある主要品目の価格を一通り取得してみる
        for rule in ITEM_RULES[:15]: # 処理時間短縮のため主要15件に限定
            canonical = rule["canonical"]
            cls = (None, None) # 以前のロジックから簡略化
            # 本来はここで各品目のコードを解決するが、一旦主要なものを取得
            # 実際にはここで e-Stat API を叩いて最新価格を集める
            # 簡易化のため、ここでは代表的なものをモック的に返すか、
            # あるいは estat_client を拡張して一括取得させる
            market_data.append({
                "item_name": canonical,
                "price": 400, # 例: 実際には API から取得
                "unit": "kg"
            })
        return market_data
    except Exception:
        return []

@app.post("/analyzeReceipt")
async def analyze_receipt(
    file: UploadFile = File(...),
    area_code: str = "00000",
):
    """
    レシート画像をAIで高度分析します。
    1. e-Statから市場価格のコンテキストを取得
    2. 画像と市場価格をGeminiに送信
    3. AIによる正規化・比較結果を返却
    """
    file_bytes = await file.read()
    
    # 1. コンテキスト（市場データ）の準備
    # 今日時点の年月を使用
    from datetime import datetime
    yyyymm = datetime.now().strftime("%Y%m")
    
    # 実際にはここでも非同期で e-Stat を叩く
    # 今回はプロンプトの威力を試すため、代表的な市場価格をコンテキストとして定義
    market_data = [
        {"item_name": "たまねぎ", "price": 418, "unit": "kg"},
        {"item_name": "にんじん", "price": 350, "unit": "kg"},
        {"item_name": "鶏卵", "price": 280, "unit": "パック(10個)"},
        {"item_name": "牛乳", "price": 250, "unit": "本(1000ml)"},
        {"item_name": "食パン", "price": 180, "unit": "袋"},
        {"item_name": "米", "price": 2500, "unit": "5kg"}
    ]

    # 2. Gemini による高度な画像解析を実行
    # プロンプト内でのノイズ除去・重量推定・比較をすべてAIに任せる
    analysis_result = await asyncio.to_thread(
        analyze_receipt_with_market_data, 
        file_bytes, 
        market_data
    )

    return analysis_result
