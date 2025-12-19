import asyncio
import time
from typing import Any, Optional
import httpx
from fastapi import HTTPException
from config import settings, CLASS_SEARCH_ORDER, ESTAT_NAME_HINTS
from services.parser import ReceiptParser 

# =================================================================
# 統計表の重要度を判定するためのキーワードと重み付けの定義
# タイトルにこれらの言葉が含まれているほど、探し求めているデータである可能性が高いと判断します
# =================================================================
ESTAT_TABLE_SCORE_WEIGHTS = [
    ("全国統一", 5), 
    ("月別", 3), 
    ("全国", 2), 
    ("価格", 1), 
    ("小売", 2), 
    ("物価", 2)
]

class EStatClient:
    def __init__(self):
        # モジュールレベルからインスタンスレベルへ移動したキャッシュ
        self._stats_data_id_cache: Optional[str] = None
        self._meta_cache: dict[str, dict[str, Any]] = {}
        self._class_map_cache: dict[str, dict[str, dict[str, str]]] = {}

    async def _get(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        if not settings.APP_ID:
            raise HTTPException(status_code=502, detail="ESTAT_APP_ID が設定されていません。")

        url = f"{settings.ESTAT_BASE_URL}/{path}"
        params = {"appId": settings.APP_ID, **params}

        async with httpx.AsyncClient(timeout=httpx.Timeout(timeout=90.0, connect=5.0)) as client:
            last_err: Optional[Exception] = None
            for i in range(3):
                try:
                    r = await client.get(url, params=params)
                    r.raise_for_status()
                    
                    try:
                        return r.json()
                    except ValueError as e:
                        raise HTTPException(
                            status_code=502, 
                            detail=f"e-Stat APIからのレスポンスがJSON形式ではありません: {e}"
                        )

                except httpx.RequestError as e:
                    last_err = e
                    await asyncio.sleep(1.0 * (i + 1))
                except httpx.HTTPStatusError as e:
                    raise HTTPException(status_code=502, detail=f"e-Stat API HTTP error: {e}") from e

            raise HTTPException(
                status_code=504, 
                detail=f"e-Stat API 接続エラー(リトライ上限超過): {last_err}"
            ) from last_err

    async def get_meta(self, statsDataId: str) -> dict[str, Any]:
        if statsDataId in self._meta_cache:
            return self._meta_cache[statsDataId]
        meta = await self._get("getMetaInfo", {"statsDataId": statsDataId})
        self._meta_cache[statsDataId] = meta
        return meta

    def extract_class_maps(self, meta_json: dict[str, Any]) -> dict[str, dict[str, str]]:
        try:
            get_meta_info = meta_json.get("GET_META_INFO", {})
            if not get_meta_info:
                raise ValueError("レスポンスに 'GET_META_INFO' が含まれていません。")
            
            metadata_inf = get_meta_info.get("METADATA_INF", {})
            if not metadata_inf:
                raise ValueError("レスポンスに 'METADATA_INF' が含まれていません。")

            class_inf = metadata_inf.get("CLASS_INF", {})
            if not class_inf:
                raise ValueError("レスポンスに 'CLASS_INF' が含まれていません。")

            class_objs = class_inf.get("CLASS_OBJ", [])
            if isinstance(class_objs, dict):
                class_objs = [class_objs]

            out: dict[str, dict[str, str]] = {}
            for obj in class_objs:
                obj_id = str(obj.get("@id", ""))
                classes = obj.get("CLASS", [])
                if isinstance(classes, dict):
                    classes = [classes]

                m: dict[str, str] = {}
                for c in classes:
                    code = str(c.get("@code", ""))
                    name = str(c.get("@name", ""))
                    if code and name:
                        m[name] = code

                if obj_id:
                    out[obj_id] = m
            return out
        except (AttributeError, KeyError) as e:
            raise ValueError(f"e-Statメタデータの解析に失敗しました(構造が不正です): {e}")

    async def get_class_maps(self, statsDataId: str) -> dict[str, dict[str, str]]:
        if statsDataId in self._class_map_cache:
            return self._class_map_cache[statsDataId]
        meta = await self.get_meta(statsDataId)
        try:
            maps = self.extract_class_maps(meta)
            self._class_map_cache[statsDataId] = maps
            return maps
        except ValueError as e:
            raise HTTPException(status_code=502, detail=str(e))

    def _table_has_any_item(self, class_maps: dict[str, dict[str, str]], keywords: list[str]) -> bool:
        from services import TextUtils
        
        # e-Statの分類ID（背番号）の意味：
        # - cat01: 品目名 (例: 卵、牛乳)
        # - cat02: 規格の詳細 (例: 10個入り、1L)
        # - cat03: その他の分類
        # - tab  : 統計の種類 (例: 小売価格)
        for obj_id in CLASS_SEARCH_ORDER:
            mp = class_maps.get(obj_id, {})
            for name in mp.keys():
                nn = TextUtils.simplify_key(name)
                for kw in keywords:
                    if TextUtils.simplify_key(kw) in nn:
                        return True
        return False

    async def pick_stats_data_id(self) -> str:
        if self._stats_data_id_cache:
            return self._stats_data_id_cache

        data = await self._get("getStatsList", {"searchWord": "小売物価統計調査 動向編 全国", "limit": 80})
        
        try:
            stats_list = data.get("GET_STATS_LIST", {})
            datalist_inf = stats_list.get("DATALIST_INF", {})
            lst = datalist_inf.get("TABLE_INF", [])
        except AttributeError:
            raise HTTPException(status_code=502, detail="統計リストのデータ構造が不正です。")

        if isinstance(lst, dict):
            lst = [lst]

        if not lst:
            raise HTTPException(status_code=502, detail="該当する統計表が見つかりませんでした。")

        def score(t: dict[str, Any]) -> int:
            title = str(t.get("TITLE", ""))
            s = 0
            # 指摘への対応: 外部で定義した定数を使用
            for kw, w in ESTAT_TABLE_SCORE_WEIGHTS:
                if kw in title:
                    s += w
            return s

        ranked = sorted(lst, key=score, reverse=True)[:25]
        must_like = ["鶏卵", "卵", "食パン", "牛乳"]

        for t in ranked:
            sid = str(t.get("@id") or t.get("ID", ""))
            if not sid:
                continue
            try:
                meta = await self.get_meta(sid)
                cm = self.extract_class_maps(meta)
                if self._table_has_any_item(cm, must_like):
                    self._stats_data_id_cache = sid
                    self._meta_cache[sid] = meta
                    self._class_map_cache[sid] = cm
                    return sid
            except (HTTPException, ValueError):
                continue

        # fallback
        best = ranked[0]
        sid = str(best.get("@id") or best.get("ID", ""))
        if not sid:
            raise HTTPException(status_code=502, detail="有効なstatsDataIdを特定できませんでした。")
        self._stats_data_id_cache = sid
        return sid

    async def lookup_stat_price(
        self,
        statsDataId: str,
        cdTime: Optional[str],
        cdArea: Optional[str],
        class_key: str,
        class_code: str,
    ) -> tuple[Optional[float], Optional[str], Optional[str]]:
        params: dict[str, Any] = {"statsDataId": statsDataId, "limit": 1}
        if cdTime:
            params["cdTime"] = cdTime
        if cdArea:
            params["cdArea"] = cdArea

        if class_key == "cat01":
            params["cdCat01"] = class_code
        elif class_key == "tab":
            params["cdTab"] = class_code
        else:
            params[f"cd{class_key[0].upper()}{class_key[1:]}"] = class_code

        data = await self._get("getStatsData", params)

        try:
            inf = data.get("GET_STATS_DATA", {}).get("STATISTICAL_DATA", {})
            datainf = inf.get("DATA_INF", {})
            values = datainf.get("VALUE", [])
        except AttributeError:
            return None, None, "レスポンスデータの解析に失敗しました。"

        if isinstance(values, dict):
            values = [values]

        if not values:
            return None, None, "VALUEが空（条件が合ってない可能性）"

        v0 = values[0]
        # 値の取得
        raw_val = v0.get("$")
        if raw_val is None:
            raw_val = v0.get("@value") or v0.get("value")

        try:
            val = float(raw_val) if raw_val is not None else None
        except (ValueError, TypeError):
            val = None

        unit = v0.get("@unit")
        return val, unit, None
