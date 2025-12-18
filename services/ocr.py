import io
import pytesseract
from functools import lru_cache
from typing import List
from PIL import Image, ImageOps, ImageFilter
from fastapi import HTTPException
from ..config import settings

# Tesseract コマンド設定
if settings.TESSERACT_CMD:
    pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_CMD

class OCRService:
    @staticmethod
    def _preprocess_for_ocr(img: Image.Image) -> Image.Image:
        g = ImageOps.grayscale(img)
        w, h = g.size
        g = g.resize((w * 2, h * 2), Image.Resampling.BICUBIC)
        g = ImageOps.autocontrast(g)
        g = g.filter(ImageFilter.UnsharpMask(radius=2, percent=150, threshold=3))
        g = g.point(lambda p: 255 if p > 160 else 0)
        return g

    @staticmethod
    @lru_cache(maxsize=1)
    def available_langs() -> List[str]:
        try:
            out = pytesseract.get_languages(config="")
            return out or []
        except Exception:
            return []

    @staticmethod
    def ocr_image(file_bytes: bytes) -> str:
        try:
            img = Image.open(io.BytesIO(file_bytes)).convert("RGB")
        except Exception:
            raise HTTPException(status_code=400, detail="画像ファイルとして読み込めませんでした。")

        proc = OCRService._preprocess_for_ocr(img)
        config = "--oem 3 --psm 6"

        langs = set(OCRService.available_langs())
        # 日本語環境がなければ英語にフォールバック
        if "jpn" in langs:
            lang = "jpn+eng" if "eng" in langs else "jpn"
        else:
            lang = "eng"

        try:
            return pytesseract.image_to_string(proc, lang=lang, config=config)
        except pytesseract.pytesseract.TesseractNotFoundError:
            raise HTTPException(status_code=500, detail="Tesseractが見つかりません。.env の TESSERACT_CMD を確認してください。")
        except pytesseract.TesseractError as e:
            raise HTTPException(status_code=500, detail=f"Tesseract error: {e}")
