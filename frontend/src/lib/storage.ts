// Local storage helpers for results and history.
import type { AnalyzeResponse, StoredResult } from "./types";

export type { StoredResult } from "./types";

const SESSION_KEY = "sessionResult";
const HISTORY_KEY = "history";

const isStoredResult = (value: unknown): value is StoredResult => {
  if (!value || typeof value !== "object") return false;
  const record = value as { id?: unknown; timestamp?: unknown; result?: unknown };
  return typeof record.id === "string" && typeof record.timestamp === "number" && typeof record.result === "object";
};

const normalizeStoredResult = (value: unknown): StoredResult | null => {
  if (isStoredResult(value)) return value;
  if (!value || typeof value !== "object") return null;
  const legacy = value as { at?: unknown; payload?: unknown };
  if (typeof legacy.at === "number" && legacy.payload && typeof legacy.payload === "object") {
    const payload = legacy.payload as AnalyzeResponse;
    const items = Array.isArray(payload.items) ? payload.items : [];
    return {
      id: String(legacy.at),
      timestamp: legacy.at,
      result: { ...payload, items }
    };
  }
  return null;
};

export function saveSessionResult(result: AnalyzeResponse): void {
  localStorage.setItem(SESSION_KEY, JSON.stringify(result));
}

export function loadSessionResult(): AnalyzeResponse | null {
  const raw = localStorage.getItem(SESSION_KEY);
  if (!raw) return null;
  try {
    const parsed = JSON.parse(raw) as AnalyzeResponse;
    if (!parsed || typeof parsed !== "object") return null;
    const items = Array.isArray(parsed.items) ? parsed.items : [];
    return { ...parsed, items };
  } catch {
    return null;
  }
}

export function saveHistory(result: StoredResult): void {
  const prev = loadHistory();
  const next = [result, ...prev];
  localStorage.setItem(HISTORY_KEY, JSON.stringify(next));
}

export function loadHistory(): StoredResult[] {
  const raw = localStorage.getItem(HISTORY_KEY);
  if (!raw) return [];
  try {
    const parsed = JSON.parse(raw) as unknown;
    if (!Array.isArray(parsed)) return [];
    return parsed.map(normalizeStoredResult).filter((item): item is StoredResult => item !== null);
  } catch {
    return [];
  }
}

export function deleteHistoryItem(id: string): void {
  const prev = loadHistory();
  const next = prev.filter((item) => item.id !== id);
  localStorage.setItem(HISTORY_KEY, JSON.stringify(next));
}

export function clearHistory(): void {
  localStorage.removeItem(HISTORY_KEY);
}
