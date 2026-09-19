"use client";

import { useEffect, useMemo, useRef, useState } from "react";

import { useLiveFeed } from "@/hooks/use-live-feed";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { stixTwoText } from "@/components/ui/Tonecard";

type Sentiment = "positive" | "negative";

type Word = {
  aspect: string;
  sentiment: Sentiment;
  count: number;
  x: number;
  y: number;
  fontSize: number;
  width: number;
  height: number;
};

type Rect = { minX: number; maxX: number; minY: number; maxY: number };

const CHART_HEIGHT = 280;
const MIN_FONT_PX = 1;
const MAX_FONT_PX = 8;
const MAX_WORDS_PER_SIDE = 100;
const GAP_PX = 6;
const PADDING_PX = 8;
const MID_GAP_PX = 12;
const FONT_WEIGHT = 500;
const FONT_FAMILY =
  '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif';

const SENTIMENT_COLOR: Record<Sentiment, string> = {
  positive: "#1F7A5C",
  negative: "#D14E38",
};

// Reused across renders instead of creating a canvas per word --
// `measureText` needs a live 2D context but never mutates it.
let measureCtx: CanvasRenderingContext2D | null = null;
function measureTextWidth(text: string, fontSizePx: number): number {
  if (!measureCtx) {
    measureCtx = document.createElement("canvas").getContext("2d");
  }
  if (!measureCtx) return text.length * fontSizePx * 0.6;
  measureCtx.font = `${FONT_WEIGHT} ${fontSizePx}px ${FONT_FAMILY}`;
  return measureCtx.measureText(text).width;
}

/**
 * Spirals every word outward from (centerX, centerY), using a
 * pixel-accurate bounding box from canvas measureText (not a guessed
 * size) so the collision check matches what's actually rendered.
 * Deliberately unbounded -- the result gets rescaled to fit its
 * target area afterwards by fitToRect, so the spiral here only has to
 * avoid overlaps, not stay on-canvas.
 */
function packCluster(
  entries: [string, number][],
  sentiment: Sentiment,
  centerX: number,
  centerY: number,
  maxCount: number
): Word[] {
  const placed: Word[] = [];

  for (const [aspect, count] of entries) {
    const t = Math.sqrt(count);
    const fontSize =  (MAX_FONT_PX - MIN_FONT_PX)*Math.pow(t,3);
    const textWidth = measureTextWidth(aspect, fontSize);
    const halfWidth = textWidth / 2 + GAP_PX / 2;
    const halfHeight = fontSize / 2 + GAP_PX / 2;

    let x = centerX;
    let y = centerY;
    let angle = 0;
    let radius = 0;
    for (let step = 0; step < 4000; step++) {
      const overlaps = placed.some(
        (p) =>
          Math.abs(p.x - x) < p.width / 2 + halfWidth &&
          Math.abs(p.y - y) < p.height / 2 + halfHeight
      );
      if (!overlaps) break;
      angle += 0.35;
      radius += 0.85;
      x = centerX + radius * Math.cos(angle);
      y = centerY + radius * Math.sin(angle) * 0.6;
    }

    placed.push({
      aspect,
      sentiment,
      count,
      x,
      y,
      fontSize,
      width: halfWidth * 2,
      height: halfHeight * 2,
    });
  }

  return placed;
}

function boundingBox(words: Word[]): Rect {
  let minX = Infinity;
  let maxX = -Infinity;
  let minY = Infinity;
  let maxY = -Infinity;
  for (const w of words) {
    minX = Math.min(minX, w.x - w.width / 2);
    maxX = Math.max(maxX, w.x + w.width / 2);
    minY = Math.min(minY, w.y - w.height / 2);
    maxY = Math.max(maxY, w.y + w.height / 2);
  }
  return { minX, maxX, minY, maxY };
}

/**
 * Rescales a cluster (in place) to occupy `rect` as fully as
 * possible, centered, without introducing overlaps:
 *   1. Shrink positions AND sizes together (a similarity transform)
 *      only if the natural layout is bigger than the rect -- scaling
 *      every distance and every box by the same factor keeps
 *      "gap between boxes" exactly as it was, so no overlap appears.
 *   2. Grow x and y independently to fill the rect edge-to-edge --
 *      this only ever moves word centers further apart (it doesn't
 *      touch box sizes), which can only shrink existing gaps'
 *      complement, never turn a non-overlap into an overlap.
 */
function fitToRect(words: Word[], rect: Rect): void {
  if (words.length === 0) return;

  const box = boundingBox(words);
  const boundW = Math.max(box.maxX - box.minX, 1e-6);
  const boundH = Math.max(box.maxY - box.minY, 1e-6);
  const cx = (box.minX + box.maxX) / 2;
  const cy = (box.minY + box.maxY) / 2;
  const targetW = rect.maxX - rect.minX;
  const targetH = rect.maxY - rect.minY;

  const shrink = Math.min(1, targetW / boundW, targetH / boundH);
  for (const w of words) {
    w.x = cx + (w.x - cx) * shrink;
    w.y = cy + (w.y - cy) * shrink;
    w.fontSize *= shrink;
    w.width *= shrink;
    w.height *= shrink;
  }

  const box2 = boundingBox(words);
  const boundW2 = Math.max(box2.maxX - box2.minX, 1e-6);
  const boundH2 = Math.max(box2.maxY - box2.minY, 1e-6);
  const cx2 = (box2.minX + box2.maxX) / 2;
  const cy2 = (box2.minY + box2.maxY) / 2;
  const growX = targetW / boundW2;
  const growY = targetH / boundH2;
  const targetCx = (rect.minX + rect.maxX) / 2;
  const targetCy = (rect.minY + rect.maxY) / 2;
  for (const w of words) {
    w.x = targetCx + (w.x - cx2) * growX;
    w.y = targetCy + (w.y - cy2) * growY;
  }
}

function topEntries(counts: Map<string, number>): [string, number][] {
  return Array.from(counts.entries())
    .sort((a, b) => b[1] - a[1])
    .slice(0, MAX_WORDS_PER_SIDE);
}

export function LiveAspectBubbles() {
  const { messages } = useLiveFeed();
  const containerRef = useRef<HTMLDivElement>(null);
  const [width, setWidth] = useState(0);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    setWidth(el.getBoundingClientRect().width);
    const observer = new ResizeObserver((entries) => {
      const entry = entries[0];
      if (entry) setWidth(entry.contentRect.width);
    });
    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  const words = useMemo(() => {
    if (width === 0) return [];

    const positiveCounts = new Map<string, number>();
    const negativeCounts = new Map<string, number>();
    for (const message of messages) {
      for (const { aspect, sentiment } of message.aspect_sentiments) {
        // Lowercase here, not just at display time, so "Food" and
        // "food" from different reviews count as the same aspect
        // instead of splitting into two separate words.
        const key = aspect.toLowerCase();
        if (sentiment === "positive") {
          positiveCounts.set(key, (positiveCounts.get(key) ?? 0) + 1);
        } else if (sentiment === "negative") {
          negativeCounts.set(key, (negativeCounts.get(key) ?? 0) + 1);
        }
      }
    }

    // Positive gets the left half, negative the right half -- each
    // cluster is packed and fit independently into its own rect, so
    // the two sides can never overlap each other regardless of how
    // lopsided the counts are.
    const midX = width / 2;
    const positiveRect: Rect = {
      minX: PADDING_PX,
      maxX: midX - MID_GAP_PX / 2,
      minY: PADDING_PX,
      maxY: CHART_HEIGHT - PADDING_PX,
    };
    const negativeRect: Rect = {
      minX: midX + MID_GAP_PX / 2,
      maxX: width - PADDING_PX,
      minY: PADDING_PX,
      maxY: CHART_HEIGHT - PADDING_PX,
    };

    const positiveEntries = topEntries(positiveCounts);
    const negativeEntries = topEntries(negativeCounts);
    // One shared max across BOTH sentiments, not one per side -- so a
    // positive aspect and a negative aspect with the same review
    // count always get the same font size, regardless of how the two
    // sides' counts compare to each other.
    const maxCount = Math.max(
      1,
      positiveEntries[0]?.[1] ?? 0,
      negativeEntries[0]?.[1] ?? 0
    );

    const positive = packCluster(
      positiveEntries,
      "positive",
      (positiveRect.minX + positiveRect.maxX) / 2,
      (positiveRect.minY + positiveRect.maxY) / 2,
      maxCount
    );
    const negative = packCluster(
      negativeEntries,
      "negative",
      (negativeRect.minX + negativeRect.maxX) / 2,
      (negativeRect.minY + negativeRect.maxY) / 2,
      maxCount
    );
    fitToRect(positive, positiveRect);
    fitToRect(negative, negativeRect);

    return [...positive, ...negative];
  }, [messages, width]);

  const hasData = words.length > 0;

  return (
    <Card className="rounded-[24px] shadow-[0_8px_16px_0_rgba(140,16,16,0.1)] ring-0 transition-shadow duration-300 hover:shadow-[0_12px_28px_0_rgba(140,16,16,0.15)]">
      <CardHeader>
        <CardTitle className={`${stixTwoText.className} text-lg text-[#260000]`}>
          Aspects in the wild
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div
          ref={containerRef}
          className="relative w-full overflow-hidden"
          style={{ height: CHART_HEIGHT }}
        >
          {words.map((word) => (
            <span
              key={`${word.sentiment}-${word.aspect}`}
              title={`${word.aspect} · ${word.sentiment} · ${word.count} review${word.count > 1 ? "s" : ""}`}
              className="absolute -translate-x-1/2 -translate-y-1/2 whitespace-nowrap leading-none"
              style={{
                left: word.x,
                top: word.y,
                fontSize: word.fontSize,
                fontWeight: FONT_WEIGHT,
                color: SENTIMENT_COLOR[word.sentiment],
              }}
            >
              {word.aspect}
            </span>
          ))}
          {!hasData && (
            <div className="absolute inset-0 flex items-center justify-center bg-white text-sm text-muted-foreground">
              Waiting for aspects to show up in incoming reviews&hellip;
            </div>
          )}
        </div>
        <div className="mt-3 flex items-center justify-center gap-6 text-xs text-[#503535]">
          <span className="flex items-center gap-1.5">
            <span className="size-2.5 rounded-full bg-[#1F7A5C]" />
            Positive
          </span>
          <span className="flex items-center gap-1.5">
            <span className="size-2.5 rounded-full bg-[#D14E38]" />
            Negative
          </span>
        </div>
      </CardContent>
    </Card>
  );
}
