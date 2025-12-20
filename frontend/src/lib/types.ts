// Shared API response and domain types for the frontend.
export type Judgement = "DEAL" | "FAIR" | "OVERPAY" | "UNKNOWN";

export type EstatResult = {
  found?: boolean;
  stat_price?: number | null;
  stat_unit?: string | null;
  diff?: number | null;
  rate?: number | null;
  judgement?: Judgement;
  note?: string | null;
};

export type ItemResult = {
  raw_name: string;
  canonical?: string | null;
  paid_unit_price: number | null;
  quantity: number | null;
  estat?: EstatResult;
};

export type AnalyzeResponse = {
  purchase_date?: string;
  summary?: {
    deal_count?: number;
    overpay_count?: number;
    unknown_count?: number;
    total_diff?: number;
  };
  items: ItemResult[];
  debug?: Record<string, unknown>;
};

export type HealthResponse = {
  ok?: boolean;
  vision_model?: string[];
  estat_app_id_set?: boolean;
};

export type MetaHit = {
  id?: string;
  class_id?: string;
  name?: string;
  code?: string;
};

export type StoredResult = {
  id: string;
  timestamp: number;
  result: AnalyzeResponse;
};
