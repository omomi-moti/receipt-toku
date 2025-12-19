import re
import unicodedata
from functools import lru_cache
from datetime import datetime
from typing import Any, Optional

from config import ITEM_RULES, UNKNOWN_RESCUE_NORMALIZE_MAP, UNKNOWN_RESCUE_CANDIDATE_RULES, CLASS_SEARCH_ORDER, EXCLUDE_WORDS, ESTAT_NAME_HINTS
from schemas import CanonicalResolution

class TextUtils:
    @staticmethod
    def normalize_text(s: str) -> str:
        s = unicodedata.normalize("NFKC", s)
        trans = str.maketrans({
            "０": "0", "１": "1", "２": "2", "３": "3", "４": "4",
            "５": "5", "６": "6", "７": "7", "８": "8", "９": "9",
            "／": "/", "－": "-", "ー": "-", "：": ":", "　": " ",
            "￥": "¥",
            "\\": "¥",
        })
        s = s.translate(trans)
        s = re.sub(r"\s+", " ", s).strip()
        return s

    @staticmethod
    def simplify_key(s: str) -> str:
        s = TextUtils.normalize_text(s)
        s = re.sub(r"[ \t\r\n]", "", s)
        s = re.sub(r"[()（）【】\[\]「」『』]", "", s)
        s = re.sub(r"[・,，\.。/／\-－]", "", s)
        return s

    @staticmethod
    def fold_key(s: str) -> str:
        return TextUtils.simplify_key(s).casefold()

class ReceiptParser:
    @staticmethod
    @lru_cache(maxsize=1)
    def _compiled_item_rules() -> list[tuple[str, list[str], list[re.Pattern[str]]]]:
        compiled: list[tuple[str, list[str], list[re.Pattern[str]]]] = []
        for rule in ITEM_RULES:
            canonical = str(rule.get("canonical") or "")
            keywords = [TextUtils.fold_key(str(k)) for k in (rule.get("keywords") or []) if k]
            patterns = [re.compile(str(p), flags=re.IGNORECASE) for p in (rule.get("patterns") or []) if p]
            compiled.append((canonical, keywords, patterns))
        return compiled

    @staticmethod
    def guess_canonical(raw: str) -> Optional[str]:
        s_norm = TextUtils.normalize_text(raw)
        s_fold = TextUtils.fold_key(s_norm)

        best: Optional[str] = None
        best_score = -1

        for canonical, keywords, patterns in ReceiptParser._compiled_item_rules():
            for pat in patterns:
                if pat.search(s_norm):
                    score = 10_000
                    if score > best_score:
                        best = canonical
                        best_score = score

            for kw in keywords:
                if kw and kw in s_fold:
                    score = len(kw)
                    if score > best_score:
                        best = canonical
                        best_score = score

        return best

    @staticmethod
    def _clean_item_name(name: str) -> str:
        name = name.strip()
        name = re.sub(r"[¥\\]+$", "", name).strip()
        name = re.sub(r"[|】\]\[]+", "", name).strip()
        return name

    @staticmethod
    def _is_excluded_name(name: str) -> bool:
        return any(w in name for w in EXCLUDE_WORDS)

    @staticmethod
    def parse_receipt_text(text: str) -> tuple[str, list[tuple[str, Optional[float]]]]:
        text_for_date = TextUtils.normalize_text(text)
        m = re.search(r"(20\d{2})[/-](\d{1,2})[/-](\d{1,2})", text_for_date)
        if m:
            y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
            purchase_date = f"{y:04d}-{mo:02d}-{d:02d}"
        else:
            purchase_date = datetime.now().strftime("%Y-%m-%d")

        items: list[tuple[str, Optional[float]]] = []
        for raw_line in text.splitlines():
            line = TextUtils.normalize_text(raw_line)
            if not line:
                continue

            if re.search(r"\b20\d{2}[/-]\d{1,2}[/-]\d{1,2}\b", line):
                continue

            m2 = re.search(r"^(.+?)\s*[¥]?\s*(\d{2,6}(?:,\d{3})*)(?:\s*円)?\s*[-‐ー*]?\s*$", line)
            if not m2:
                continue

            name = ReceiptParser._clean_item_name(m2.group(1))
            amt_s = m2.group(2).replace(",", "")

            if not name or len(name) <= 1 or ReceiptParser._is_excluded_name(name):
                continue

            if not re.search(r"[A-Za-zぁ-んァ-ン一-龥]", name):
                continue

            try:
                price = float(amt_s)
            except Exception:
                price = None

            items.append((name, price))

        return purchase_date, items

    @staticmethod
    def _candidate_terms_for_unknown(raw_name: str) -> list[str]:
        raw_norm = TextUtils.normalize_text(raw_name)
        raw_fold = TextUtils.fold_key(raw_norm)

        out: list[str] = []

        for k, v in UNKNOWN_RESCUE_NORMALIZE_MAP.items():
            if k and TextUtils.fold_key(k) in raw_fold:
                out.append(v)
                break

        for rule in UNKNOWN_RESCUE_CANDIDATE_RULES:
            match_any = [str(x) for x in (rule.get("match_any") or [])]
            match_all = [str(x) for x in (rule.get("match_all") or [])]
            match_patterns = [str(x) for x in (rule.get("match_patterns") or [])]
            candidates = [str(x) for x in (rule.get("candidates") or [])]

            ok = False
            if match_any and any(TextUtils.fold_key(x) in raw_fold for x in match_any if x):
                ok = True
            if match_all and all(TextUtils.fold_key(x) in raw_fold for x in match_all if x):
                ok = True
            if match_patterns and any(re.search(p, raw_norm, flags=re.IGNORECASE) for p in match_patterns if p):
                ok = True

            if ok:
                out.extend(candidates)

        stripped = re.sub(r"\d+(\s*[gGmMlL])?", "", raw_norm).strip()
        if stripped and stripped != raw_norm:
            out.append(stripped)

        uniq: list[str] = []
        seen: set[str] = set()
        for x in out:
            if not x:
                continue
            k = TextUtils.fold_key(x)
            if k in seen:
                continue
            seen.add(k)
            uniq.append(x)
        return uniq

    @staticmethod
    def _iter_class_name_hits(class_maps: dict[str, dict[str, str]], q: str, limit: int = 80) -> list[dict[str, str]]:
        qq = TextUtils.simplify_key(q)
        if not qq:
            return []

        hits: list[dict[str, str]] = []
        for obj_id in CLASS_SEARCH_ORDER:
            mp = class_maps.get(obj_id) or {}
            for name, code in mp.items():
                if qq in TextUtils.simplify_key(name):
                    hits.append({"class_id": obj_id, "name": name, "code": code})
                    if len(hits) >= limit:
                        return hits
        return hits

    @staticmethod
    def _pick_best_hit(hits: list[dict[str, str]]) -> Optional[dict[str, str]]:
        if not hits:
            return None

        def score(h: dict[str, str]) -> tuple[int, int, int, int, str]:
            name = h.get("name") or ""
            class_id = h.get("class_id") or ""
            simple_len = len(TextUtils.simplify_key(name)) or 10**9
            has_digits = 1 if re.search(r"\d", name) else 0
            class_pri = CLASS_SEARCH_ORDER.index(class_id) if class_id in CLASS_SEARCH_ORDER else 999
            return (simple_len, has_digits, class_pri, len(name), name)

        return sorted(hits, key=score)[0]

    @staticmethod
    def resolve_canonical(raw_name: str, class_maps: dict[str, dict[str, str]]) -> CanonicalResolution:
        canonical = ReceiptParser.guess_canonical(raw_name)
        if canonical:
            return CanonicalResolution(canonical=canonical)

        candidates = ReceiptParser._candidate_terms_for_unknown(raw_name)
        tried: list[dict[str, Any]] = []

        all_hits: list[dict[str, str]] = []
        for term in candidates:
            hits = ReceiptParser._iter_class_name_hits(class_maps, term, limit=80)
            all_hits.extend(hits)
            tried.append(
                {
                    "term": term,
                    "hits": len(hits),
                    "samples": hits[:3],
                }
            )

        picked = ReceiptParser._pick_best_hit(all_hits)
        if not picked:
            tried_sorted = sorted(tried, key=lambda d: int(d.get("hits") or 0), reverse=True)[:3]
            return CanonicalResolution(canonical=None, candidates_debug=tried_sorted)

        tried_sorted = sorted(tried, key=lambda d: int(d.get("hits") or 0), reverse=True)[:3]
        return CanonicalResolution(
            canonical=picked.get("name"),
            class_id=picked.get("class_id"),
            class_code=picked.get("code"),
            candidates_debug=tried_sorted,
        )
    
    @staticmethod
    def classify_to_code(class_maps: dict[str, dict[str, str]], canonical: str) -> Optional[tuple[str, str]]:
        hints = ESTAT_NAME_HINTS.get(canonical, [canonical])
        canon_s = TextUtils.simplify_key(canonical)

        for obj_id in ["cat01", "tab", "cat02", "cat03"]:
            mp = class_maps.get(obj_id)
            if not mp:
                continue

            if canonical in mp:
                return obj_id, mp[canonical]

            for name, code in mp.items():
                for h in hints:
                    if h and h in name:
                        return obj_id, code

            for name, code in mp.items():
                if canonical in name:
                    return obj_id, code

            for name, code in mp.items():
                if canon_s and canon_s in TextUtils.simplify_key(name):
                    return obj_id, code

        return None
    
    @staticmethod
    def suggest_meta_candidates(class_maps: dict[str, dict[str, str]], canonical: str, limit: int = 10) -> list[dict[str, str]]:
        hints = ESTAT_NAME_HINTS.get(canonical, [canonical])
        keys = [TextUtils.simplify_key(h) for h in hints if h]
        hits: list[dict[str, str]] = []

        for obj_id in ["cat01", "tab", "cat02", "cat03"]:
            mp = class_maps.get(obj_id) or {}
            for name, code in mp.items():
                nn = TextUtils.simplify_key(name)
                if any(k and k in nn for k in keys):
                    hits.append({"class": obj_id, "name": name, "code": code})
                    if len(hits) >= limit:
                        return hits
        return hits
    
    @staticmethod
    def resolve_time_code(class_maps: dict[str, dict[str, str]], yyyymm: str) -> tuple[str, Optional[str]]:
        time_map = class_maps.get("time") or {}
        if not time_map:
            return ("time", None)

        y = int(yyyymm[:4])
        m = int(yyyymm[4:6])

        for name, code in time_map.items():
            if yyyymm == code or yyyymm == name:
                return ("time", code)

        patterns = [
            rf"{y}\s*年\s*0?{m}\s*月",
            rf"{y}\s*[\-/\]\s*0?{m}",
            rf"{y}\s*0?{m}",
        ]
        for name, code in time_map.items():
            nn = TextUtils.normalize_text(name)
            if any(re.search(p, nn) for p in patterns):
                return ("time", code)

        return ("time", None)

    @staticmethod
    def resolve_area_code(class_maps: dict[str, dict[str, str]], requested: str) -> tuple[str, Optional[str]]:
        area_map = class_maps.get("area") or {}
        if not area_map:
            return ("area", None)

        codes = set(area_map.values())
        if requested in codes:
            return ("area", requested)

        for key in area_map.keys():
            if "全国" in key or "全国平均" in key or "全域" in key:
                return ("area", area_map[key])

        first_name = next(iter(area_map.keys()))
        return ("area", area_map[first_name])

    @staticmethod
    def yyyymm_from_date(purchase_date: str) -> str:
        dt = datetime.strptime(purchase_date, "%Y-%m-%d")
        return f"{dt.year:04d}{dt.month:02d}"
