import time
from typing import Any, Dict, List, Optional, Tuple
import requests
from fastapi import HTTPException
from ..config import settings, CLASS_SEARCH_ORDER, ESTAT_NAME_HINTS
from ..services.parser import ReceiptParser # 循環参照の可能性に注意、必要な関数だけutilsにする手もあるが一旦これで作る

# モジュールレベルキャッシュ (簡易的なインメモリキャッシュ)
_STATS_DATA_ID_CACHE: Optional[str] = None
_META_CACHE: Dict[str, Dict[str, Any]] = {}
_CLASS_MAP_CACHE: Dict[str, Dict[str, Dict[str, str]]] = {}

class EStatClient:
    def __init__(self):
        # スレッドセーフにするため、リクエスト毎にセッションを作るか、あるいは
        # requests.get を直接使う。ここでは単純化のため requests.get を使う。
        # 必要ならコネクションプーリングの設定をした session を依存性注入で渡す設計にする。
        pass

    def _get(self, path: str, params: Dict[str, Any]) -> Dict[str, Any]:
        if not settings.APP_ID:
            raise HTTPException(status_code=500, detail="ESTAT_APP_ID が設定されていません。")

        url = f"{settings.ESTAT_BASE_URL}/{path}"
        params = {"appId": settings.APP_ID, **params}

        last_err: Optional[Exception] = None
        for i in range(3):
            try:
                # タイムアウトを設定
                r = requests.get(url, params=params, timeout=(5, 90))
                r.raise_for_status()
                return r.json()
            except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError) as e:
                last_err = e
                time.sleep(1.0 * (i + 1))
            except requests.exceptions.HTTPError as e:
                raise HTTPException(status_code=502, detail=f"e-Stat API HTTP error: {e}") from e

        raise HTTPException(status_code=504, detail=f"e-Stat API timeout/connection error: {last_err}") from last_err

    def get_meta(self, statsDataId: str) -> Dict[str, Any]:
        if statsDataId in _META_CACHE:
            return _META_CACHE[statsDataId]
        meta = self._get("getMetaInfo", {"statsDataId": statsDataId})
        _META_CACHE[statsDataId] = meta
        return meta

    def extract_class_maps(self, meta_json: Dict[str, Any]) -> Dict[str, Dict[str, str]]:
        meta = ((((meta_json.get("GET_META_INFO") or {}).get("METADATA_INF") or {}).get("CLASS_INF") or {}))
        class_objs = meta.get("CLASS_OBJ") or []
        if isinstance(class_objs, dict):
            class_objs = [class_objs]

        out: Dict[str, Dict[str, str]] = {}
        for obj in class_objs:
            obj_id = str(obj.get("@id") or "")
            classes = obj.get("CLASS") or []
            if isinstance(classes, dict):
                classes = [classes]

            m: Dict[str, str] = {}
            for c in classes:
                code = str(c.get("@code") or "")
                name = str(c.get("@name") or "")
                if code and name:
                    m[name] = code

            if obj_id:
                out[obj_id] = m
        return out

    def get_class_maps(self, statsDataId: str) -> Dict[str, Dict[str, str]]:
        if statsDataId in _CLASS_MAP_CACHE:
            return _CLASS_MAP_CACHE[statsDataId]
        meta = self.get_meta(statsDataId)
        maps = self.extract_class_maps(meta)
        _CLASS_MAP_CACHE[statsDataId] = maps
        return maps

    def _table_has_any_item(self, class_maps: Dict[str, Dict[str, str]], keywords: List[str]) -> bool:
        # 循環参照を避けるため簡易実装、または外部からパーサーロジックの一部を借りる
        # ここでは単純な文字列マッチングで実装
        from ..services.parser import TextUtils
        
        for obj_id in ["cat01", "tab", "cat02", "cat03"]:
            mp = class_maps.get(obj_id) or {}
            for name in mp.keys():
                nn = TextUtils.simplify_key(name)
                for kw in keywords:
                    if TextUtils.simplify_key(kw) in nn:
                        return True
        return False

    def pick_stats_data_id(self) -> str:
        global _STATS_DATA_ID_CACHE
        if _STATS_DATA_ID_CACHE:
            return _STATS_DATA_ID_CACHE

        data = self._get("getStatsList", {"searchWord": "小売物価統計調査 動向編 全国", "limit": 80})
        lst = ((((data.get("GET_STATS_LIST") or {}).get("DATALIST_INF") or {}).get("TABLE_INF")) or [])
        if isinstance(lst, dict):
            lst = [lst]

        if not lst:
            raise HTTPException(status_code=502, detail="getStatsList が空でした。")

        def score(t: Dict[str, Any]) -> int:
            title = str(t.get("TITLE") or "")
            s = 0
            for kw, w in [("全国統一", 5), ("月別", 3), ("全国", 2), ("価格", 1), ("小売", 2), ("物価", 2)]:
                if kw in title:
                    s += w
            return s

        ranked = sorted(lst, key=score, reverse=True)[:25]
        must_like = ["鶏卵", "卵", "食パン", "牛乳"]

        for t in ranked:
            sid = str(t.get("@id") or t.get("ID") or "")
            if not sid:
                continue
            try:
                meta = self.get_meta(sid)
                cm = self.extract_class_maps(meta)
                if self._table_has_any_item(cm, must_like):
                    _STATS_DATA_ID_CACHE = sid
                    _META_CACHE[sid] = meta
                    _CLASS_MAP_CACHE[sid] = cm
                    return sid
            except HTTPException:
                continue

        # fallback
        best = ranked[0]
        sid = str(best.get("@id") or best.get("ID") or "")
        if not sid:
            raise HTTPException(status_code=502, detail="statsDataId を取得できませんでした。")
        _STATS_DATA_ID_CACHE = sid
        return sid

    def lookup_stat_price(
        self,
        statsDataId: str,
        cdTime: Optional[str],
        cdArea: Optional[str],
        class_key: str,
        class_code: str,
    ) -> Tuple[Optional[float], Optional[str], Optional[str]]:
        params: Dict[str, Any] = {"statsDataId": statsDataId, "limit": 1}
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

        data = self._get("getStatsData", params)

        inf = (data.get("GET_STATS_DATA") or {}).get("STATISTICAL_DATA") or {}
        datainf = inf.get("DATA_INF") or {}
        values = datainf.get("VALUE") or []
        if isinstance(values, dict):
            values = [values]

        if not values:
            return None, None, "VALUEが空（条件が合ってない可能性）"

        v0 = values[0]
        raw_val = v0.get("$") if isinstance(v0, dict) else None
        if raw_val is None and isinstance(v0, dict):
            raw_val = v0.get("@value") or v0.get("value")

        try:
            val = float(raw_val)
        except Exception:
            val = None

        unit = v0.get("@unit") if isinstance(v0, dict) else None
        return val, unit, None
