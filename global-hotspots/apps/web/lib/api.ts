const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

const DEMO_TOKEN = "demo-token";

type RequestOptions = {
  method?: "GET" | "POST" | "PATCH";
  body?: unknown;
  revalidate?: number | false;
};

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { method = "GET", body, revalidate = 30 } = options;
  const res = await fetch(`${API_BASE}${path}`, {
    method,
    headers: {
      Authorization: `Bearer ${DEMO_TOKEN}`,
      ...(body ? { "Content-Type": "application/json" } : {}),
    },
    ...(body ? { body: JSON.stringify(body) } : {}),
    ...(method === "GET" ? (revalidate === false ? { cache: "no-store" as const } : { next: { revalidate } }) : {}),
  });
  if (!res.ok) {
    throw new Error(`Request failed: ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export async function getGlobePoints(window = "24h") {
  return request(`/api/v1/globe/points?window=${encodeURIComponent(window)}`);
}

export async function getHotspots(window = "24h") {
  return request(`/api/v1/hotspots?window=${encodeURIComponent(window)}`);
}

export async function getRankings(window = "24h") {
  return request(`/api/v1/rankings?window=${encodeURIComponent(window)}&limit=20`);
}

export type ProviderItem = {
  provider: string;
  model: string;
  base_url: string | null;
  is_default: boolean;
  key_preview: string;
};

export type SourceItem = {
  source_id: number;
  name: string;
  source_type: string;
  region: string;
  language: string;
  reliability_score: number;
  enabled: boolean;
  weight: number;
  crawl_interval_minutes: number;
  keyword_allowlist: string[];
  keyword_blocklist: string[];
};

export type SourceConnectivityItem = {
  source_id: number;
  status: "ok" | "error" | "skipped";
  latency_ms: number | null;
  detail: string | null;
};

export type SourcePreviewOut = {
  source_id: number;
  source_name: string;
  status: "ok" | "error";
  count: number;
  detail: string | null;
  items: Array<{
    title: string;
    summary: string;
  }>;
};

export async function listProviders() {
  return request<ProviderItem[]>("/api/v1/settings/ai-providers", { revalidate: false });
}

export async function upsertProvider(payload: {
  provider: string;
  api_key: string;
  model: string;
  base_url?: string | null;
  is_default?: boolean;
}) {
  return request<ProviderItem>("/api/v1/settings/ai-key", {
    method: "POST",
    body: payload,
  });
}

export async function listSources() {
  return request<SourceItem[]>("/api/v1/sources", { revalidate: false });
}

export async function updateSourceConfig(
  sourceId: number,
  payload: {
    enabled?: boolean;
    weight?: number;
    crawl_interval_minutes?: number;
    keyword_allowlist?: string[];
    keyword_blocklist?: string[];
  },
) {
  return request<SourceItem>(`/api/v1/sources/${sourceId}`, {
    method: "PATCH",
    body: payload,
  });
}

export async function refreshEvents() {
  return request<{
    ingest: { sources?: number; fetched?: number; inserted?: number; error?: string };
    score: { events?: number; scores?: number; error?: string };
    status: "ok" | "partial";
    stages: { ingest: "ok" | "error"; score: "ok" | "error" };
  }>(
    "/api/v1/refresh",
    {
      method: "POST",
    },
  );
}

export async function getRuntimeProxy() {
  return request<{ source_proxy_url: string | null }>("/api/v1/settings/runtime/proxy", { revalidate: false });
}

export async function setRuntimeProxy(source_proxy_url: string | null) {
  return request<{ source_proxy_url: string | null }>("/api/v1/settings/runtime/proxy", {
    method: "POST",
    body: { source_proxy_url },
  });
}

export async function getSourceConnectivity() {
  return request<SourceConnectivityItem[]>("/api/v1/sources/connectivity", { revalidate: false });
}

export async function previewSource(sourceId: number, limit = 5) {
  return request<SourcePreviewOut>(`/api/v1/sources/${sourceId}/preview?limit=${limit}`, {
    method: "POST",
  });
}
