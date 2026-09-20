"use client";

import { useEffect, useState } from "react";

import { getHealth } from "@/lib/api";

const POLL_INTERVAL_MS = 3000;

// A failed getHealth() during a Render cold start (connection
// refused/timeout while the container is still spinning up) is the
// expected, normal case here -- not an error to surface, just a
// reason to try again shortly.
export function useBackendReady(): boolean {
  const [ready, setReady] = useState(false);

  useEffect(() => {
    let cancelled = false;
    let timeout: ReturnType<typeof setTimeout> | null = null;

    async function check() {
      try {
        await getHealth();
        if (!cancelled) setReady(true);
      } catch {
        if (!cancelled) timeout = setTimeout(check, POLL_INTERVAL_MS);
      }
    }

    check();

    return () => {
      cancelled = true;
      if (timeout) clearTimeout(timeout);
    };
  }, []);

  return ready;
}
