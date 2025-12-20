// Minimal API client wrappers for the frontend.
import { AnalyzeResponse, HealthResponse, MetaHit } from "./types";

const BASE_URL = (import.meta.env.VITE_API_BASE_URL as string | undefined) || "";

const buildUrl = (path: string) => {
  if (!BASE_URL) return path;
  const base = BASE_URL.endsWith("/") ? BASE_URL.slice(0, -1) : BASE_URL;
  const suffix = path.startsWith("/") ? path : `/${path}`;
  return `${base}${suffix}`;
};

async function request<T>(path: string, opts: RequestInit = {}): Promise<T> {
  const url = buildUrl(path);
  let res: Response;
  try {
    res = await fetch(url, opts);
  } catch (err) {
    const msg = err instanceof Error ? err.message : "通信に失敗しました";
    throw new Error(msg);
  }

  const text = await res.text();
  let data: unknown = null;
  if (text) {
    try {
      data = JSON.parse(text);
    } catch {
      throw new Error("レスポンスの解析に失敗しました");
    }
  }

  if (!res.ok) {
    const detail =
      data && typeof data === "object" && ("detail" in data || "message" in data)
        ? String((data as { detail?: unknown; message?: unknown }).detail ?? (data as { message?: unknown }).message ?? "")
        : res.statusText;
    throw new Error(`HTTP ${res.status}${detail ? `: ${detail}` : ""}`);
  }

  return data as T;
}

export async function healthCheck(): Promise<HealthResponse> {
  return request<HealthResponse>("/health");
}

export async function metaSearch(keyword: string): Promise<MetaHit[]> {
  const params = new URLSearchParams({ q: keyword });
  const res = await request<MetaHit[] | { hits?: MetaHit[] }>(`/metaSearch?${params.toString()}`);
  return Array.isArray(res) ? res : res?.hits ?? [];
}

export async function analyzeReceipt(file: File): Promise<AnalyzeResponse> {
  const form = new FormData();
  form.append("file", file);
  return request<AnalyzeResponse>("/analyzeReceipt", {
    method: "POST",
    body: form
  });
}
