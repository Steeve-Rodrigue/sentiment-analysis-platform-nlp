export function buildLiveWsUrl(): string {
  const base = process.env.API_URL ?? "http://localhost:5000";
  return base.replace(/^http/, "ws") + "/api/live";
}
