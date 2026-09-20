"use client";

import type { ReactNode } from "react";

import { useBackendReady } from "@/hooks/use-backend-ready";
import { BackendLoading } from "@/components/backend-loading";

export function BackendGate({ children }: { children: ReactNode }) {
  const ready = useBackendReady();
  return ready ? <>{children}</> : <BackendLoading />;
}
