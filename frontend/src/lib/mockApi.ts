// Mock API responses for local/demo usage.
import { AnalyzeResponse, HealthResponse, ItemResult, MetaHit } from "./types";

const MOCK_DELAY_MS = 350;

const mockItems: ItemResult[] = [
  {
    raw_name: "Milk 1L",
    canonical: "Milk",
    paid_unit_price: 198,
    quantity: 1,
    estat: {
      found: true,
      stat_price: 210,
      diff: -12,
      rate: -0.057,
      judgement: "DEAL",
      note: "Slightly cheaper than average"
    }
  },
  {
    raw_name: "Bread (6 slices)",
    canonical: "Bread",
    paid_unit_price: 168,
    quantity: 1,
    estat: {
      found: true,
      stat_price: 160,
      diff: 8,
      rate: 0.05,
      judgement: "OVERPAY",
      note: "A bit higher than average"
    }
  },
  {
    raw_name: "Eggs (10 pack)",
    canonical: "Eggs",
    paid_unit_price: 258,
    quantity: 1,
    estat: {
      found: true,
      stat_price: 260,
      diff: -2,
      rate: -0.008,
      judgement: "DEAL",
      note: "Close to average"
    }
  },
  {
    raw_name: "Seasonal juice",
    canonical: null,
    paid_unit_price: 238,
    quantity: 1,
    estat: {
      found: false,
      stat_price: null,
      diff: null,
      rate: null,
      judgement: "UNKNOWN",
      note: "No matching stats found"
    }
  },
  {
    raw_name: "Tomatoes (2 packs)",
    canonical: "Tomatoes",
    paid_unit_price: 120,
    quantity: 2,
    estat: {
      found: true,
      stat_price: 110,
      diff: 10,
      rate: 0.091,
      judgement: "OVERPAY",
      note: "Market price lower"
    }
  },
  {
    raw_name: "Bananas (1 bunch)",
    canonical: "Bananas",
    paid_unit_price: 158,
    quantity: 1,
    estat: {
      found: true,
      stat_price: 170,
      diff: -12,
      rate: -0.071,
      judgement: "DEAL",
      note: "Discounted today"
    }
  },
  {
    raw_name: "Tofu (2 blocks)",
    canonical: "Tofu",
    paid_unit_price: 98,
    quantity: 2,
    estat: {
      found: true,
      stat_price: 100,
      diff: -2,
      rate: -0.02,
      judgement: "DEAL",
      note: "Slightly below average"
    }
  },
  {
    raw_name: "Chicken breast 400g",
    canonical: "Chicken breast",
    paid_unit_price: 420,
    quantity: 1,
    estat: {
      found: true,
      stat_price: 400,
      diff: 20,
      rate: 0.05,
      judgement: "OVERPAY",
      note: "Higher than average"
    }
  },
  {
    raw_name: "Instant noodles (5 pack)",
    canonical: "Instant noodles",
    paid_unit_price: 298,
    quantity: 1,
    estat: {
      found: true,
      stat_price: 280,
      diff: 18,
      rate: 0.064,
      judgement: "OVERPAY",
      note: "Store price higher"
    }
  },
  {
    raw_name: "Cereal bar",
    canonical: null,
    paid_unit_price: 148,
    quantity: 1,
    estat: {
      found: false,
      stat_price: null,
      diff: null,
      rate: null,
      judgement: "UNKNOWN",
      note: "No matching stats found"
    }
  }
];

const mockAnalyzeResponse: AnalyzeResponse = {
  purchase_date: "2024-04-01",
  summary: {
    deal_count: 4,
    overpay_count: 4,
    unknown_count: 2,
    total_diff: 28
  },
  items: mockItems,
  debug: {
    source: "mock",
    ocr_lines: [
      "Milk 1L 198",
      "Bread 6 slices 168",
      "Eggs 10 pack 258",
      "Seasonal juice 238",
      "Tomatoes 2 packs 120",
      "Bananas 1 bunch 158",
      "Tofu 2 blocks 98",
      "Chicken breast 400g 420",
      "Instant noodles 5 pack 298",
      "Cereal bar 148"
    ],
    hint: "Set VITE_USE_MOCK=true to always use mock data."
  }
};

const mockMetaHits: MetaHit[] = [
  { class_id: "0113", name: "Bread", code: "011301" },
  { class_id: "0113", name: "Rolls", code: "011302" },
  { class_id: "0114", name: "Milk", code: "011401" },
  { class_id: "0114", name: "Yogurt", code: "011402" },
  { class_id: "0115", name: "Eggs", code: "011501" },
  { class_id: "0116", name: "Tofu", code: "011601" },
  { class_id: "0117", name: "Chicken", code: "011701" },
  { class_id: "0118", name: "Tomatoes", code: "011801" },
  { class_id: "0118", name: "Bananas", code: "011802" },
  { class_id: "0119", name: "Juice", code: "011901" },
  { class_id: "0119", name: "Instant noodles", code: "011902" },
  { class_id: "0120", name: "Cereal bar", code: "012001" }
];

const mockHealthResponse: HealthResponse = {
  ok: true,
  vision_model: ["mock-vision-v1"],
  estat_app_id_set: true
};

const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

const filterHits = (query: string) => {
  const q = query.trim();
  if (!q) return mockMetaHits;
  const lower = q.toLowerCase();
  const hits = mockMetaHits.filter((hit) => {
    const name = hit.name || "";
    const code = hit.code || "";
    return name.includes(q) || name.toLowerCase().includes(lower) || code.includes(q);
  });
  return hits.length > 0 ? hits : mockMetaHits.slice(0, 3);
};

export async function mockRequest<T>(path: string): Promise<T> {
  await sleep(MOCK_DELAY_MS);
  const [pathname, search] = path.split("?");

  if (pathname === "/health") {
    return mockHealthResponse as T;
  }
  if (pathname === "/metaSearch") {
    const params = new URLSearchParams(search || "");
    const q = params.get("q") || "";
    return { statsDataId: "mock-2024", hits: filterHits(q) } as T;
  }
  if (pathname === "/analyzeReceipt") {
    return mockAnalyzeResponse as T;
  }

  throw new Error(`Mock API: unsupported endpoint ${pathname}`);
}

export function shouldUseMock(baseUrl: string) {
  const flag = import.meta.env.VITE_USE_MOCK as string | undefined;
  if (flag === "true") return true;
  if (flag === "false") return false;
  return !baseUrl && import.meta.env.DEV;
}

export function shouldFallbackToMock(baseUrl: string, err: unknown) {
  const flag = import.meta.env.VITE_USE_MOCK as string | undefined;
  if (flag === "false") return false;
  if (!import.meta.env.DEV || baseUrl) return false;
  if (err instanceof TypeError) return true;
  if (err instanceof Error && err.message.startsWith("HTTP 404")) return true;
  return false;
}
