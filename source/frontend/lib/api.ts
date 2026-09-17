import type {
  AnalyzeResponse,
  HealthResponse,
  SentimentResponse,
} from "@/lib/types";

// Server-rendered code (e.g. the /models page) runs inside the
// frontend container and must reach the backend over the Docker
// network (API_BASE_URL_INTERNAL=http://backend:8000 in
// docker-compose.yml). Client code runs in the viewer's browser and
// must use a host-reachable URL instead (NEXT_PUBLIC_API_BASE_URL).
function resolveBaseUrl(): string {
  if (typeof window === "undefined") {
    return (
      process.env.API_BASE_URL_INTERNAL ??
      process.env.NEXT_PUBLIC_API_BASE_URL ??
      "http://localhost:8000"
    );
  }
  return process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
}

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${resolveBaseUrl()}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });

  if (!res.ok) {
    throw new Error(`API ${path} failed: ${res.status} ${await res.text()}`);
  }

  return res.json() as Promise<T>;
}

export function getHealth(): Promise<HealthResponse> {
  return apiFetch<HealthResponse>("/api/health", { cache: "no-store" });
}

export function postSentiment(text: string): Promise<SentimentResponse> {
  return apiFetch<SentimentResponse>("/api/sentiment", {
    method: "POST",
    body: JSON.stringify({ text }),
  });
}

export function postAnalyzeAspects(
  text: string,
  aspects?: string[],
): Promise<AnalyzeResponse> {
  return apiFetch<AnalyzeResponse>("/api/aspects/analyze", {
    method: "POST",
    body: JSON.stringify({ text, aspects: aspects ?? null }),
  });
}
