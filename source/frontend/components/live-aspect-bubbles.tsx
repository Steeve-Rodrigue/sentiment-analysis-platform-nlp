"use client";

import { useMemo } from "react";
import ReactECharts from "echarts-for-react";

import { useLiveFeed } from "@/hooks/use-live-feed";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { kadwa } from "@/components/ui/Tonecard";

type Sentiment = "positive" | "negative";

type Bubble = {
  aspect: string;
  sentiment: Sentiment;
  count: number;
  x: number;
  y: number;
  r: number;
};

const MIN_RADIUS = 14;
const MAX_RADIUS = 42;
const MAX_BUBBLES_PER_SIDE = 10;

/** Places circles around (centerX, centerY) with a tight spiral
 * search so bigger bubbles (sorted first) settle near the center and
 * none overlap -- good enough for a small, unevenly-sized bubble
 * cluster without pulling in a dedicated packing library. Capped to
 * the top MAX_BUBBLES_PER_SIDE most frequent aspects so the layout
 * stays readable instead of growing unbounded as more reviews land. */
function packBubbles(
  counts: Map<string, number>,
  centerX: number,
  centerY: number,
  sentiment: Sentiment
): Bubble[] {
  const entries = Array.from(counts.entries())
    .sort((a, b) => b[1] - a[1])
    .slice(0, MAX_BUBBLES_PER_SIDE);
  const maxCount = entries.length > 0 ? entries[0][1] : 1;
  const placed: { x: number; y: number; r: number }[] = [];

  return entries.map(([aspect, count]) => {
    const r = MIN_RADIUS + (MAX_RADIUS - MIN_RADIUS) * Math.sqrt(count / maxCount);
    let x = centerX;
    let y = centerY;
    let angle = 0;
    let radius = 0;
    for (let step = 0; step < 5000; step++) {
      const overlaps = placed.some((p) => {
        const dx = p.x - x;
        const dy = p.y - y;
        return Math.hypot(dx, dy) < p.r + r + 2;
      });
      if (!overlaps) break;
      angle += 0.25;
      radius += 0.4;
      x = centerX + radius * Math.cos(angle);
      y = centerY + radius * Math.sin(angle);
    }
    placed.push({ x, y, r });
    return { aspect, sentiment, count, x, y, r };
  });
}

export function LiveAspectBubbles() {
  const { messages } = useLiveFeed();

  const { positive, negative } = useMemo(() => {
    const positiveCounts = new Map<string, number>();
    const negativeCounts = new Map<string, number>();
    for (const message of messages) {
      for (const { aspect, sentiment } of message.aspect_sentiments) {
        if (sentiment === "positive") {
          positiveCounts.set(aspect, (positiveCounts.get(aspect) ?? 0) + 1);
        } else if (sentiment === "negative") {
          negativeCounts.set(aspect, (negativeCounts.get(aspect) ?? 0) + 1);
        }
      }
    }
    const positive = packBubbles(positiveCounts, -70, 0, "positive");
    const negative = packBubbles(negativeCounts, 70, 0, "negative");
    return { positive, negative };
  }, [messages]);

  const hasData = positive.length > 0 || negative.length > 0;

  // Size the axes to whatever the packing actually produced instead of
  // a guessed fixed range -- avoids clipping bubbles when there are
  // many distinct aspects, and avoids a mostly-empty chart when there
  // are few.
  const { xRange, yRange } = useMemo(() => {
    const all = [...positive, ...negative];
    let maxAbsX = 90;
    let maxAbsY = 50;
    for (const b of all) {
      maxAbsX = Math.max(maxAbsX, Math.abs(b.x) + b.r);
      maxAbsY = Math.max(maxAbsY, Math.abs(b.y) + b.r);
    }
    return {
      xRange: maxAbsX + 10,
      yRange: maxAbsY + 10,
    };
  }, [positive, negative]);

  const option = {
    tooltip: {
      formatter: (params: { data: Bubble }) =>
        `${params.data.aspect}<br/>${params.data.sentiment} &middot; ${params.data.count} review${params.data.count > 1 ? "s" : ""}`,
    },
    xAxis: { type: "value", min: -xRange, max: xRange, show: false },
    yAxis: { type: "value", min: -yRange, max: yRange, show: false },
    series: [
      {
        type: "scatter",
        data: positive,
        symbolSize: (_value: unknown, params: { data: Bubble }) => params.data.r * 2,
        itemStyle: { color: "#1F7A5C", opacity: 0.85 },
        label: {
          show: true,
          formatter: (p: { data: Bubble }) => p.data.aspect,
          color: "#fff",
          fontSize: 11,
          overflow: "truncate",
        },
        encode: { x: "x", y: "y" },
        dimensions: ["x", "y"],
      },
      {
        type: "scatter",
        data: negative,
        symbolSize: (_value: unknown, params: { data: Bubble }) => params.data.r * 2,
        itemStyle: { color: "#D14E38", opacity: 0.85 },
        label: {
          show: true,
          formatter: (p: { data: Bubble }) => p.data.aspect,
          color: "#fff",
          fontSize: 11,
          overflow: "truncate",
        },
        encode: { x: "x", y: "y" },
        dimensions: ["x", "y"],
      },
    ],
  };

  return (
    <Card className="rounded-[24px] shadow-[0_8px_16px_0_rgba(140,16,16,0.1)] ring-0 transition-shadow duration-300 hover:shadow-[0_12px_28px_0_rgba(140,16,16,0.15)]">
      <CardHeader>
        <CardTitle className={`${kadwa.className} text-lg text-[#260000]`}>
          Aspects in the wild
        </CardTitle>
      </CardHeader>
      <CardContent>
        {hasData ? (
          <ReactECharts option={option} style={{ height: 280 }} notMerge />
        ) : (
          <div className="flex h-[280px] items-center justify-center text-sm text-muted-foreground">
            Waiting for aspects to show up in incoming reviews&hellip;
          </div>
        )}
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
