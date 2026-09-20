"use client";

import { useEffect } from "react";

import { getHealth } from "@/lib/api";

// Render's free tier spins the backend down after inactivity and
// takes ~30-60s to cold-start it back up. Firing this as soon as the
// landing page loads (instead of waiting for the user to reach
// /sentiment) gives that cold start a head start. Fire-and-forget: a
// failed request here (connection refused/timeout while the
// container is still spinning up, or a CORS rejection) is expected
// and irrelevant -- we only care that the request was sent.
export function BackendWarmup() {
  useEffect(() => {
    getHealth().catch(() => {});
  }, []);

  return null;
}
