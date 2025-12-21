"""
e-Stat APIから市場価格データを取得するモジュール
"""
import asyncio
import time
from datetime import datetime

from loguru import logger
from schemas import EStatClient

# グローバルキャッシュ
_market_data_cache: list[dict[str, str | float]] = []
_cache_timestamp: float = 0
CACHE_TTL = 86400  # 24時間

# 同時接続数制限
MAX_CONCURRENT_REQUESTS = 10

# 食料品目コードの範囲（小売物価統計の品目分類）
# 01xxx: 食料（穀類、魚介類、肉類、乳卵類、野菜・海藻、果物、油脂・調味料、菓子類、調理食品、飲料、外食）
# 02xxx: 酒類
FOOD_CODE_PREFIXES = ("01", "02")


async def _fetch_single_item(
    estat_client: EStatClient,
    stats_data_id: str,
    item_name: str,
    item_code: str,
    cd_time: str | None,
    class_key: str,
    semaphore: asyncio.Semaphore,
) -> dict[str, str | float] | None:
    """
    単一品目の価格を取得
    """
    async with semaphore:
        try:
            price, unit, error = await estat_client.lookup_stat_price(
                statsDataId=stats_data_id,
                cdTime=cd_time,
                cdArea="13100",  # 東京特別区部（全国データがないため代表都市を使用）
                class_key=class_key,
                class_code=item_code,
            )
            if price is not None:
                # 品目名から番号プレフィックスを削除 (例: "1341 鶏卵" → "鶏卵")
                clean_name = item_name
                if " " in item_name:
                    parts = item_name.split(" ", 1)
                    if parts[0].isdigit():
                        clean_name = parts[1]

                return {
                    "item_name": clean_name,
                    "price": price,
                    "unit": unit or "",
                }
            else:
                logger.debug(f"価格取得失敗: {item_name} - {error}")
                return None
        except Exception as e:
            logger.warning(f"品目取得エラー: {item_name} - {e}")
            return None


def _get_current_time_code() -> str:
    """
    現在の年月からe-Stat時間コードを生成
    形式: YYYY00MMDD (例: 2025年11月 → "2025001111")
    ※DDはMMと同じ値が使われる
    """
    now = datetime.now()
    # e-Statの時間コードは "YYYY00MMDD" 形式 (DDはMMと同じ)
    # 最新データは1-2ヶ月遅れなので、前月のデータを使用
    month = now.month - 1 if now.month > 1 else 12
    year = now.year if now.month > 1 else now.year - 1
    return f"{year}00{month:02d}{month:02d}"


async def fetch_all_market_data(
    estat_client: EStatClient | None = None,
) -> list[dict[str, str | float]]:
    """
    e-Stat APIから全品目の市場価格を取得（キャッシュ付き）

    戻り値: [{"item_name": "鶏卵", "price": 280.0, "unit": "パック(10個)"}, ...]
    """
    global _market_data_cache, _cache_timestamp

    # キャッシュが有効ならそれを返す
    if _market_data_cache and (time.time() - _cache_timestamp) < CACHE_TTL:
        logger.debug(f"市場データをキャッシュから取得 ({len(_market_data_cache)}品目)")
        return _market_data_cache

    if estat_client is None:
        estat_client = EStatClient()

    try:
        # 統計表IDを取得
        stats_data_id = await estat_client.pick_stats_data_id()
        logger.info(f"統計表ID: {stats_data_id}")

        # 品目分類マップを取得
        # 統計表によってcat01またはcat02に品目が格納されている
        class_maps = await estat_client.get_class_maps(stats_data_id)
        item_class_key = "cat01"
        items = class_maps.get("cat01", {})
        # cat01が1件以下の場合はcat02を使用（品目データは通常cat02に格納）
        if len(items) <= 1:
            item_class_key = "cat02"
            items = class_maps.get("cat02", {})

        if not items:
            logger.warning("品目が見つかりませんでした")
            return _market_data_cache if _market_data_cache else []

        # 食料品目のみ抽出（コードが1で始まるもの）& 調査終了品目を除外
        food_items = {
            name: code for name, code in items.items()
            if code.startswith(FOOD_CODE_PREFIXES) and "調査終了" not in name
        }
        logger.info(f"取得対象品目数: {len(food_items)}/{len(items)} (食料品目のみ、調査終了除外)")

        # 現在の時間コード
        cd_time = _get_current_time_code()
        logger.info(f"時間コード: {cd_time}")

        # 並列で価格を取得
        semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
        tasks = [
            _fetch_single_item(
                estat_client=estat_client,
                stats_data_id=stats_data_id,
                item_name=name,
                item_code=code,
                cd_time=cd_time,
                class_key=item_class_key,
                semaphore=semaphore,
            )
            for name, code in food_items.items()
        ]

        results = await asyncio.gather(*tasks)

        # Noneを除外
        market_data = [r for r in results if r is not None]

        logger.info(f"市場データ取得完了: {len(market_data)}/{len(food_items)}品目")

        # キャッシュを更新
        _market_data_cache = market_data
        _cache_timestamp = time.time()

        return market_data

    except Exception as e:
        logger.error(f"市場データ取得エラー: {e}")
        # エラー時は最後のキャッシュを返す
        if _market_data_cache:
            logger.info("キャッシュからフォールバック")
            return _market_data_cache
        return []


def get_cached_market_data() -> list[dict[str, str | float]]:
    """
    キャッシュされた市場データを取得（API呼び出しなし）
    """
    return _market_data_cache


def clear_market_data_cache() -> None:
    """
    市場データキャッシュをクリア
    """
    global _market_data_cache, _cache_timestamp
    _market_data_cache = []
    _cache_timestamp = 0
    logger.info("市場データキャッシュをクリアしました")
