"use client";

import { useState } from "react";

import { postAnalyzeAspects } from "@/lib/api";
import type { AnalyzeResponse } from "@/lib/types";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { SentimentBadge } from "@/components/sentiment-badge";
import { kadwa } from "@/components/ui/Tonecard";

export function AspectForm() {
  const [text, setText] = useState("");
  const [aspectsInput, setAspectsInput] = useState("");
  const [result, setResult] = useState<AnalyzeResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError(null);
    const aspects = aspectsInput
      .split(",")
      .map((aspect) => aspect.trim())
      .filter(Boolean);
    try {
      setResult(
        await postAnalyzeAspects(text, aspects.length > 0 ? aspects : undefined),
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Request failed");
      setResult(null);
    } finally {
      setLoading(false);
    }
  }

  return (
    <Card className="rounded-[24px] shadow-[0_8px_16px_0_rgba(140,16,16,0.1)] ring-0 transition-shadow duration-300 hover:shadow-[0_12px_28px_0_rgba(209,78,56,0.15)]">
      <CardHeader>
        <CardTitle className={`${kadwa.className} text-[14] text-[#260000]`}>
          Aspect-based sentiment
        </CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        <div className="rounded-lg bg-[#f2f0f0] p-3 text-[10px] text-[#503535] sm:text-xs">
          <p className="font-medium text-[#260000] ">Example</p>
          <p className="mt-1 italic">
            &ldquo;The delivery was late, but the support team was great and
            the price was fair.&rdquo;
          </p>
          <p className="mt-2 flex flex-wrap gap-x-4 gap-y-1">
            <span>
              delivery: <span className="font-medium text-[#D14E38]">negative</span>
            </span>
            <span>
              support: <span className="font-medium text-[#1F7A5C]">positive</span>
            </span>
            <span>
              price: <span className="font-medium text-[#1F7A5C]">positive</span>
            </span>
          </p>
        </div>

        <form onSubmit={handleSubmit} className="flex flex-col gap-3">
          <Textarea
            placeholder="Type a customer review..."
            value={text}
            onChange={(event) => setText(event.target.value)}
            minLength={1}
            maxLength={5000}
            required
            className="focus-visible:border-[#D14E38] focus-visible:ring-[#D14E38]/50"
          />
           <Button
            type="submit"
            disabled={loading || text.length === 0}
            className="bg-gradient-to-r from-[#1040b9] to-[#3a67ed] text-white hover:opacity-90"
          >
            {loading ? "Analyzing..." : "Analyze aspects"}
          </Button>
        </form>
        {error && <p className="text-sm text-destructive">{error}</p>}
        {result && (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Aspect</TableHead>
                <TableHead>Sentiment</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {result.aspects.map((item) => (
                <TableRow key={item.aspect}>
                  <TableCell>{item.aspect}</TableCell>
                  <TableCell>
                    <SentimentBadge sentiment={item.sentiment} />
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </CardContent>
    </Card>
  );
}
