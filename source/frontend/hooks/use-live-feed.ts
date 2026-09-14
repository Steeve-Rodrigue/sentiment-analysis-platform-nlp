"use client";

import { useEffect, useRef, useState } from "react";

import { buildLiveWsUrl } from "@/lib/ws";
import type { LiveReviewMessage } from "@/lib/types";

const MAX_MESSAGES = 50;
const RECONNECT_DELAY_MS = 2000;

export type LiveFeedStatus = "connecting" | "open" | "reconnecting" | "closed";

export function useLiveFeed() {
  const [messages, setMessages] = useState<LiveReviewMessage[]>([]);
  const [status, setStatus] = useState<LiveFeedStatus>("connecting");
  const manuallyClosedRef = useRef(false);

  useEffect(() => {
    manuallyClosedRef.current = false;
    let socket: WebSocket | null = null;
    let reconnectTimeout: ReturnType<typeof setTimeout> | null = null;

    function connect() {
      socket = new WebSocket(buildLiveWsUrl());

      socket.onopen = () => setStatus("open");

      socket.onmessage = (event) => {
        const message = JSON.parse(event.data) as LiveReviewMessage;
        setMessages((prev) => [...prev.slice(-(MAX_MESSAGES - 1)), message]);
      };

      socket.onclose = () => {
        if (manuallyClosedRef.current) {
          setStatus("closed");
          return;
        }
        setStatus("reconnecting");
        reconnectTimeout = setTimeout(connect, RECONNECT_DELAY_MS);
      };

      socket.onerror = () => socket?.close();
    }

    connect();

    return () => {
      manuallyClosedRef.current = true;
      if (reconnectTimeout) clearTimeout(reconnectTimeout);
      socket?.close();
    };
  }, []);

  return {
    messages,
    latest: messages[messages.length - 1],
    status,
  };
}
