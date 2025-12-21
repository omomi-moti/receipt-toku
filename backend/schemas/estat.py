import asyncio

import httpx
from config import settings
from fastapi import HTTPException
from rules import CLASS_SEARCH_ORDER

from .parser import simplify_key

# e-Stat APIレスポンス用の型エイリアス
type JsonValue = str | int | float | bool | None | dict[str, "JsonValue"] | list["JsonValue"]
type JsonDict = dict[str, JsonValue]

ESTAT_TABLE_SCORE_WEIGHTS = [
    ("全国統一", 5),
    ("月別", 3),
    ("全国", 2),
    ("価格", 1),
    ("小売", 2),
    ("物価", 2)
]


def _calculate_stats_table_score(table_info: JsonDict) -> int:
    """統計表のタイトルから、探し物（小売物価統計）である可能性をスコア化します。"""
    title = str(table_info.get("TITLE", ""))
    score = 0
    # 定義した重み付けリスト（定数）を使用して計算
    for keyword, weight in ESTAT_TABLE_SCORE_WEIGHTS:
        if keyword in title:
            score += weight
    return score


class EStatClient:
    """
    EStatClient の Docstring
    """
    def __init__(self) -> None:
        # モジュールレベルからインスタンスレベルへ移動したキャッシュ
        self._stats_data_id_cache: str | None = None
        self._meta_cache: dict[str, JsonDict] = {}
        self._class_map_cache: dict[str, dict[str, dict[str, str]]] = {}

    async def _get(self, path: str, params: dict[str, str | int]) -> JsonDict:
        if not settings.ESTAT_APP_ID:
            raise HTTPException(status_code=502, detail="ESTAT_APP_ID が設定されていません。")

        url = f"{settings.ESTAT_BASE_URL}/{path}"
        full_params: dict[str, str | int] = {"appId": settings.ESTAT_APP_ID, **params}

        async with httpx.AsyncClient(timeout=httpx.Timeout(timeout=90.0, connect=5.0)) as client:
            last_err: Exception | None = None
            for i in range(3):
                try:
                    r = await client.get(url, params=full_params)
                    r.raise_for_status()
                    try:
                        result: JsonDict = r.json()
                        return result
                    except ValueError as e:
                        raise HTTPException(
                            status_code=502,
                            detail=f"e-Stat APIからのレスポンスがJSON形式ではありません: {str(e)} from e"
                        )from e

                except httpx.RequestError as e:
                    last_err = e
                    await asyncio.sleep(1.0 * (i + 1))
                except httpx.HTTPStatusError as e:
                    raise HTTPException(status_code=502, detail=f"e-Stat API HTTP error: {e}") from e

            raise HTTPException(
                status_code=504,
                detail=f"e-Stat API 接続エラー(リトライ上限超過): {last_err}"
            ) from last_err

    async def get_meta(self, statsDataId: str) -> JsonDict:
        if statsDataId in self._meta_cache:
            return self._meta_cache[statsDataId]
        meta = await self._get("getMetaInfo", {"statsDataId": statsDataId})
        self._meta_cache[statsDataId] = meta
        return meta

    def extract_class_maps(self, meta_json: JsonDict) -> dict[str, dict[str, str]]:
        try:
            get_meta_info = meta_json.get("GET_META_INFO")
            if not isinstance(get_meta_info, dict):
                raise ValueError("レスポンスに 'GET_META_INFO' が含まれていません。")
            metadata_inf = get_meta_info.get("METADATA_INF")
            if not isinstance(metadata_inf, dict):
                raise ValueError("レスポンスに 'METADATA_INF' が含まれていません。")

            class_inf = metadata_inf.get("CLASS_INF")
            if not isinstance(class_inf, dict):
                raise ValueError("レスポンスに 'CLASS_INF' が含まれていません。")

            class_objs_raw = class_inf.get("CLASS_OBJ", [])
            if not isinstance(class_objs_raw, list):
                class_objs_raw = []

            out: dict[str, dict[str, str]] = {}
            for obj in class_objs_raw:
                if not isinstance(obj, dict):
                    continue
                obj_id = str(obj.get("@id", ""))
                classes_raw = obj.get("CLASS", [])
                # CLASSが単一オブジェクトの場合はリストに変換
                if isinstance(classes_raw, dict):
                    classes: list[JsonDict] = [classes_raw]
                elif isinstance(classes_raw, list):
                    classes = [c for c in classes_raw if isinstance(c, dict)]
                else:
                    classes = []

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
            raise ValueError(f"e-Statメタデータの解析に失敗しました(構造が不正です): {e}") from e

    async def get_class_maps(self, statsDataId: str) -> dict[str, dict[str, str]]:
        if statsDataId in self._class_map_cache:
            return self._class_map_cache[statsDataId]
        meta = await self.get_meta(statsDataId)
        try:
            maps = self.extract_class_maps(meta)
            self._class_map_cache[statsDataId] = maps
            return maps
        except ValueError as e:
            raise HTTPException(status_code=502, detail=str(e))from e

    def _table_has_any_item(self, class_maps: dict[str, dict[str, str]], keywords: list[str]) -> bool:
        # e-Statの分類ID（背番号）の意味：
        # - cat01: 品目名 (例: 卵、牛乳)
        # - cat02: 規格の詳細 (例: 10個入り、1L)
        # - cat03: その他の分類
        # - tab  : 統計の種類 (例: 小売価格)
        for obj_id in CLASS_SEARCH_ORDER:
            mp = class_maps.get(obj_id, {})
            for name in mp.keys():
                nn = simplify_key(name)
                for kw in keywords:
                    if simplify_key(kw) in nn:
                        return True
        return False

    async def pick_stats_data_id(self) -> str:
        if self._stats_data_id_cache:
            return self._stats_data_id_cache

        data = await self._get("getStatsList", {"searchWord": "小売物価統計調査 動向編 全国", "limit": 80})
        try:
            stats_list = data.get("GET_STATS_LIST")
            if not isinstance(stats_list, dict):
                raise HTTPException(status_code=502, detail="統計リストのデータ構造が不正です。")
            datalist_inf = stats_list.get("DATALIST_INF")
            if not isinstance(datalist_inf, dict):
                raise HTTPException(status_code=502, detail="統計リストのデータ構造が不正です。")
            lst = datalist_inf.get("TABLE_INF", [])
        except AttributeError as exc:
            raise HTTPException(status_code=502, detail='統計リストのデータ構造が不正です。:{exc}') from exc

        if isinstance(lst, dict):
            lst = [lst]
        elif not isinstance(lst, list):
            lst = []

        if not lst:
            raise HTTPException(status_code=502, detail="該当する統計表が見つかりませんでした。")

        # 独立させたスコア計算関数を使用して並び替え
        table_list: list[JsonDict] = [t for t in lst if isinstance(t, dict)]
        ranked = sorted(table_list, key=_calculate_stats_table_score, reverse=True)[:25]
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
        cdTime: str | None,
        cdArea: str | None,
        class_key: str,
        class_code: str,
    ) -> tuple[float | None, str | None, str | None]:
        params: dict[str, str | int] = {"statsDataId": statsDataId, "limit": 1}
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
            get_stats_data = data.get("GET_STATS_DATA")
            if not isinstance(get_stats_data, dict):
                return None, None, "レスポンスデータの解析に失敗しました"
            statistical_data = get_stats_data.get("STATISTICAL_DATA")
            if not isinstance(statistical_data, dict):
                return None, None, "レスポンスデータの解析に失敗しました"
            data_inf = statistical_data.get("DATA_INF")
            if not isinstance(data_inf, dict):
                return None, None, "レスポンスデータの解析に失敗しました"
            values_raw = data_inf.get("VALUE", [])
        except AttributeError:
            return None, None, "レスポンスデータの解析に失敗しました"

        if not values_raw:
            return None, None, "VALUEが空（条件が合ってない可能性）"

        # valuesが単一オブジェクトの場合はリストに変換
        if isinstance(values_raw, dict):
            values: list[JsonDict] = [values_raw]
        elif isinstance(values_raw, list):
            values = [v for v in values_raw if isinstance(v, dict)]
        else:
            return None, None, "VALUEの形式が不正です"

        if not values:
            return None, None, "VALUEが空（条件が合ってない可能性）"

        v0 = values[0]
        # 値の取得
        raw_val = v0.get("$")
        if raw_val is None:
            raw_val = v0.get("@value") or v0.get("value")

        try:
            val = float(str(raw_val)) if raw_val is not None else None
        except (ValueError, TypeError):
            val = None

        unit_val = v0.get("@unit")
        unit: str | None = str(unit_val) if unit_val is not None else None
        return val, unit, None
