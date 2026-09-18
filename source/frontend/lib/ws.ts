export function buildLiveWsUrl(): string {
  const base = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:5000";
  return base.replace(/^http/, "ws") + "/api/live";
}
