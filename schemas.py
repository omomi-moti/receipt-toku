from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class EstatResult(BaseModel):
    found: bool
    stat_price: Optional[float] = None
    stat_unit: Optional[str] = None
    diff: Optional[float] = None
    rate: Optional[float] = None
    judgement: str = "UNKNOWN"
    note: Optional[str] = None

class ItemResult(BaseModel):
    raw_name: str
    canonical: Optional[str]
    paid_unit_price: Optional[float]
    quantity: Optional[float] = 1
    estat: EstatResult

class AnalyzeResponse(BaseModel):
    purchase_date: str
    currency: str = "JPY"
    items: List[ItemResult]
    summary: Dict[str, Any]
    debug: Dict[str, Any]

class CanonicalResolution(BaseModel):
    canonical: Optional[str] = None
    class_id: Optional[str] = None
    class_code: Optional[str] = None
    candidates_debug: List[Dict[str, Any]] = Field(default_factory=list)
