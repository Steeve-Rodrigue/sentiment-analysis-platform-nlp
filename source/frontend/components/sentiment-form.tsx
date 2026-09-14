"use client";

import { useState } from "react";

import { postSentiment } from "@/lib/api";
import type { SentimentResponse } from "@/lib/types";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { SentimentBadge } from "@/components/sentiment-badge";
import { kadwa } from "@/components/ui/Tonecard";

export function SentimentForm() {
  const [text, setText] = useState("");
  const [result, setResult] = useState<SentimentResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError(null);
    try {
      setResult(await postSentiment(text));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Request failed");
      setResult(null);
    } finally {
      setLoading(false);
    }
  }

  return (
    <Card className="rounded-[24px] shadow-[0_8px_16px_0_rgba(140,16,16,0.1)] ring-0 transition-shadow duration-300 hover:shadow-[0_12px_28px_0_rgba(16,64,185,0.15)]">
      <CardHeader>
        <CardTitle className={`${kadwa.className} text-[14] text-[#260000]`}>
          Global sentiment
        </CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        <form onSubmit={handleSubmit} className="flex flex-col gap-3 ">
          <Textarea
            placeholder="Type a customer review..."
            value={text}
            onChange={(event) => setText(event.target.value)}
            minLength={1}
            maxLength={5000}
            required
            className="focus-visible:border-[#3a67ed] focus-visible:ring-[#3a67ed]/50"
          />
          <Button
            type="submit"
            disabled={loading || text.length === 0}
            className="bg-gradient-to-r from-[#1040b9] to-[#3a67ed] text-white hover:opacity-90"
          >
            {loading ? "Analyzing..." : "Analyze sentiment"}
          </Button>
        </form>
        {error && <p className="text-sm text-destructive">{error}</p>}
        {result && (
          <div className="flex items-center gap-2 text-sm">
            <SentimentBadge sentiment={result.sentiment} />
            <span className="text-muted-foreground">
              {result.processing_time_ms.toFixed(1)} ms
            </span>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
