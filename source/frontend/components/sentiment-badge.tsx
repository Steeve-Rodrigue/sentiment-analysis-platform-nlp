import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

const SENTIMENT_STYLES: Record<string, string> = {
  positive: "bg-[#DCEFE6] text-[#1F7A5C]",
  negative: "bg-[#FBE2DC] text-[#D14E38]",
  neutral: "bg-[#f2f0f0] text-[#503535]",
};

export function SentimentBadge({ sentiment }: { sentiment: string }) {
  return (
    <Badge className={cn(SENTIMENT_STYLES[sentiment])}>{sentiment}</Badge>
  );
}
