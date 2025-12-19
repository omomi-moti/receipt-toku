from typing import Any, Optional
from pydantic import BaseModel, Field

# =================================================================
# e-Stat 検索結果のスキーマ
# =================================================================

class EstatResult(BaseModel):
    found: bool = Field(description="e-Statで統計価格が見つかったかどうか")
    stat_price: Optional[float] = Field(None, description="e-Statから取得した平均価格")
    stat_unit: Optional[str] = Field(None, description="統計価格の単位（例: 100g, 1パック）")
    diff: Optional[float] = Field(None, description="支払価格と統計価格の差額")
    rate: Optional[float] = Field(None, description="統計価格に対する乖離率（0.1 = +10%）")
    judgement: str = Field("UNKNOWN", description="価格の妥当性判断（DEAL, OVERPAY, FAIR, UNKNOWN）")
    note: Optional[str] = Field(None, description="補足情報やエラー理由")

# =================================================================
# 商品ごとの解析結果スキーマ
# =================================================================

class ItemResult(BaseModel):
    raw_name: str = Field(description="レシートに記載されていた元の名前")
    canonical: Optional[str] = Field(None, description="名寄せ後の標準的な商品名")
    paid_unit_price: Optional[float] = Field(None, description="レシートから抽出した支払単価")
    quantity: Optional[float] = Field(1.0, description="購入数量")
    estat: EstatResult = Field(description="e-Statとの比較結果の詳細")

# =================================================================
# API全体のレスポンススキーマ
# =================================================================

class AnalyzeResponse(BaseModel):
    purchase_date: str = Field(description="レシートから読み取った購入日（YYYY-MM-DD）")
    currency: str = Field("JPY", description="通貨単位")
    items: list[ItemResult] = Field(description="解析された各商品のリスト")
    summary: dict[str, Any] = Field(description="解析結果の全体サマリー（合計差額など）")
    debug: dict[str, Any] = Field(description="デバッグ用の内部情報（OCRテキスト、マッチング候補など）")

# =================================================================
# 商品名の名寄せ（正規化）結果
# =================================================================

class CanonicalResolution(BaseModel):
    canonical: Optional[str] = Field(None, description="解決された標準名称")
    class_id: Optional[str] = Field(None, description="e-StatのカテゴリID")
    class_code: Optional[str] = Field(None, description="e-Statの項目コード")
    candidates_debug: list[dict[str, Any]] = Field(default_factory=list, description="名寄せの際に検討された候補（デバッグ用）")