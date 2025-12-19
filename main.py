import asyncio
import re
from typing import Any, Optional

from fastapi import FastAPI, File, UploadFile, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from schemas import AnalyzeResponse, ItemResult, EstatResult
from services import EStatClient, VisionService, ReceiptParser, normalize_text, simplify_key, fold_key, judge

app = FastAPI(title="Receipt Deal Checker (e-Stat)", version="mvp-stable-5a-gemini")

# 必要に応じてCORS設定などを追加
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
        "vision_model": VisionService.get_model_name(),
        "estat_app_id_set": bool(settings.APP_ID),
    }

@app.get("/health")
def health():
    return {
        "ok": True,
        "vision_model": VisionService.get_model_name(),
        "estat_app_id_set": bool(settings.APP_ID),
    }

@app.get("/metaSearch")
async def meta_search(q: str = Query(..., description="例: 食パン / 鶏卵 / 卵 など")):
    statsDataId = await estat_client.pick_stats_data_id()
    class_maps = await estat_client.get_class_maps(statsDataId)

    hits: list[dict[str, str]] = []
    # Parserのロジックを借りて検索
    hits = ReceiptParser._iter_class_name_hits(class_maps, q, limit=50)
    
    return {"statsDataId": statsDataId, "hits": hits}

@app.post("/analyzeReceipt", response_model=AnalyzeResponse)
async def analyze_receipt(
    file: UploadFile = File(...),
    area_code: str = "00000",
    debug_ocr: bool = False,
):
    b = await file.read()
    
    # ブロッキングなLLM API呼び出しをスレッドプールで実行
    text = await asyncio.to_thread(VisionService.extract_text_from_image, b)

    candidate_lines: list[str] = []
    for line in text.splitlines():
        s = normalize_text(line)
        if s and re.search(r"\d{2,6}", s):
            candidate_lines.append(s)

    purchase_date, parsed_items = ReceiptParser.parse_receipt_text(text)
    yyyymm = ReceiptParser.yyyymm_from_date(purchase_date)

    if debug_ocr:
        debug_extra = {
            "ocr_text_head": normalize_text(text)[:1200],
            "ocr_lines_with_digits": candidate_lines[:60],
            "parsed_items": parsed_items[:30],
        }
        canonical_candidates_debug: list[dict[str, Any]] = []
    else:
        debug_extra = {}
        canonical_candidates_debug = []

    try:
        statsDataId = await estat_client.pick_stats_data_id()
        class_maps = await estat_client.get_class_maps(statsDataId)
        
        _, cdTime = ReceiptParser.resolve_time_code(class_maps, yyyymm)
        _, cdArea = ReceiptParser.resolve_area_code(class_maps, area_code)
        
    except HTTPException as e:
        results = []
        for raw_name, price in parsed_items[:30]:
            results.append(
                ItemResult(
                    raw_name=raw_name,
                    canonical=ReceiptParser.guess_canonical(raw_name),
                    paid_unit_price=price,
                    quantity=1,
                    estat=EstatResult(found=False, judgement="UNKNOWN", note=f"e-Stat unavailable: {e.detail}"),
                )
            )
        return AnalyzeResponse(
            purchase_date=purchase_date,
            items=results,
            summary={"deal_count": 0, "overpay_count": 0, "unknown_count": len(results), "total_diff": 0.0},
            debug={
                "statsDataId": None,
                "requested_area_code": area_code,
                "time_code_from_receipt": yyyymm,
                "resolved_cdArea": None,
                "resolved_cdTime": None,
                **debug_extra,
            },
        )

    results: list[ItemResult] = []
    deal = overpay = unknown = 0
    total_diff = 0.0

    for raw_name, price in parsed_items[:30]:
        if ReceiptParser._is_excluded_name(raw_name):
            continue

        resolution = ReceiptParser.resolve_canonical(raw_name, class_maps)
        canonical = resolution.canonical

        cls: tuple[str, Optional[str]] = None
        if resolution.class_id and resolution.class_code:
            cls = (resolution.class_id, resolution.class_code)

        if canonical and price is not None:
            if not cls:
                cls = ReceiptParser.classify_to_code(class_maps, canonical)

            if not cls:
                unknown += 1
                sugg = ReceiptParser.suggest_meta_candidates(class_maps, canonical, limit=10)
                note = "item not in meta (try /metaSearch)"
                if sugg:
                    note += f" candidates={sugg[:3]} (showing 3)"
                estat = EstatResult(found=False, judgement="UNKNOWN", note=note)
                results.append(ItemResult(raw_name=raw_name, canonical=canonical, paid_unit_price=price, quantity=1, estat=estat))
                if debug_ocr:
                    tried = resolution.candidates_debug
                    if not tried and sugg:
                        tried = [{"term": canonical, "hits": len(sugg), "samples": sugg[:3]}]
                    canonical_candidates_debug.append(
                        {
                            "raw_name": raw_name,
                            "canonical": canonical,
                            "selected": None,
                            "tried": tried[:3],
                        }
                    )
                continue

            class_key, class_code = cls
            
            # API call
            stat_price, stat_unit, note = await estat_client.lookup_stat_price(
                statsDataId, cdTime, cdArea, class_key, class_code
            )

            if stat_price is not None:
                diff, rate, j = judge(price, stat_price)
                total_diff += diff
                if j == "DEAL":
                    deal += 1
                elif j == "OVERPAY":
                    overpay += 1
                estat = EstatResult(found=True, stat_price=stat_price, stat_unit=stat_unit, diff=diff, rate=rate, judgement=j, note=note)
            else:
                unknown += 1
                estat = EstatResult(found=False, judgement="UNKNOWN", note=note or "not found")
        else:
            unknown += 1
            estat = EstatResult(found=False, judgement="UNKNOWN", note="no canonical match or no price")

        results.append(ItemResult(raw_name=raw_name, canonical=canonical, paid_unit_price=price, quantity=1, estat=estat))

        if debug_ocr and estat.judgement == "UNKNOWN":
            canonical_candidates_debug.append(
                {
                    "raw_name": raw_name,
                    "canonical": canonical,
                    "selected": {"class_id": cls[0], "class_code": cls[1]} if cls else None,
                    "tried": resolution.candidates_debug[:3],
                }
            )

    return AnalyzeResponse(
        purchase_date=purchase_date,
        items=results,
        summary={"deal_count": deal, "overpay_count": overpay, "unknown_count": unknown, "total_diff": total_diff},
        debug={
            "statsDataId": statsDataId,
            "requested_area_code": area_code,
            "time_code_from_receipt": yyyymm,
            "resolved_cdArea": cdArea,
            "resolved_cdTime": cdTime,
            "canonical_candidates": canonical_candidates_debug[:50] if debug_ocr else [],
            **debug_extra,
        },
    )
