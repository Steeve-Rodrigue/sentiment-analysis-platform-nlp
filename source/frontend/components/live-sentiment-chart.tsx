"use client";

import ReactECharts from "echarts-for-react";

import { useLiveFeed } from "@/hooks/use-live-feed";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { kadwa } from "@/components/ui/Tonecard";

const STATUS_LABEL: Record<string, string> = {
  connecting: "Connecting...",
  open: "Live",
  reconnecting: "Reconnecting...",
  closed: "Closed",
};

export function LiveSentimentChart() {
  const { messages, status } = useLiveFeed();

  const lastMessage =
    messages.length > 0 ? messages[messages.length - 1] : null;
  const lastScore = lastMessage ? lastMessage.overall_score : 0;
  const trendColor = lastScore >= 0 ? "#1F7A5C" : "#D14E38";

  const option = {
    grid: { left: 40, right: 20, top: 20, bottom: 30 },
    xAxis: {
      type: "category",
      data: messages.map((message) => message.received_at),
      show: false,
    },
    yAxis: {
      type: "value",
      min: -1,
      max: 1,
      splitLine: {
      lineStyle: {
        type: 'dashed',
        opacity : 0.8
        }
      }
    },
    tooltip: {
      trigger: "axis",
      formatter: (params: { dataIndex: number }[]) => {
        const message = messages[params[0]?.dataIndex];
        if (!message) return "";
        return `${message.text.slice(0, 80)}<br/>score: ${message.overall_score.toFixed(2)}`;
      },
    },
    series: [
      {
        type: "line",
        smooth: false,
        lineStyle: { width: 2, color: trendColor },
        data: messages.map((message) => message.overall_score),
      },
    ],
  };

  return (
    <Card className="rounded-[24px] shadow-[0_8px_16px_0_rgba(140,16,16,0.1)] ring-0 transition-shadow duration-300 hover:shadow-[0_12px_28px_0_rgba(15,35,134,0.15)]">
      <CardHeader className="flex flex-row items-center justify-between">
        <div>
          <CardTitle className={`${kadwa.className} text-lg text-[#260000]`}>
            Live review stream
          </CardTitle>
        </div>
        <span
          className={
            status === "open"
              ? "inline-flex items-center gap-1.5 rounded-full bg-[#DCEFE6] px-2.5 py-1 text-xs font-medium text-[#1F7A5C]"
              : "inline-flex items-center gap-1.5 rounded-full bg-[#f2f0f0] px-2.5 py-1 text-xs font-medium text-[#503535]"
          }
        >
          <span
            className={
              status === "open"
                ? "size-1.5 rounded-full bg-[#1F7A5C] animate-pulse"
                : "size-1.5 rounded-full bg-[#503535]/60"
            }
          />
          {STATUS_LABEL[status]}
        </span>
      </CardHeader>
      <CardContent className="flex flex-col gap-3">
        <ReactECharts option={option} style={{ height: 280 }} notMerge />
        <div className="flex items-center gap-2 rounded-lg bg-[#f2f0f0] p-3 text-xs text-[#503535]">
          <span
            className="size-2 rounded-full"
            style={{
              backgroundColor: lastMessage ? trendColor : "#50353566",
            }}
          />
          <p className="flex-1 italic">
            {lastMessage
              ? `“${lastMessage.text}”`
              : "Waiting for the next review…"}
          </p>
          {lastMessage && (
            <span
              className="font-medium"
              style={{ color: trendColor }}
            >
              {lastMessage.overall_score.toFixed(2)}
            </span>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
