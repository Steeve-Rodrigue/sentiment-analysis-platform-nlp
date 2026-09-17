export interface HealthResponse {
  status: string;
  models_ready: boolean;
}

export interface SentimentResponse {
  text: string;
  sentiment: "positive" | "negative";
  confidence: number;
  processing_time_ms: number;
}

export interface AspectSentiment {
  aspect: string;
  sentiment: "positive" | "negative" | "neutral";
}

export interface AnalyzeResponse {
  text: string;
  aspects: AspectSentiment[];
  confidence: number;
  processing_time_ms: number;
}


export interface LiveReviewMessage {
  review_id: number;
  text: string;
  aspect_sentiments: AspectSentiment[];
  overall_score: number;
  received_at: string;
}
