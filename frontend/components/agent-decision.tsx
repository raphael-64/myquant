"use client";

import { useState, useEffect } from "react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import {
  ArrowUpIcon,
  ArrowDownIcon,
  MinusIcon,
  Brain,
  TrendingUp,
  BarChart3,
  LineChart,
} from "lucide-react";

interface AgentDecisionProps {
  stockSymbol: string;
  priceData: any[];
  sentimentData: any[];
}

export default function AgentDecision({
  stockSymbol,
  priceData,
  sentimentData,
}: AgentDecisionProps) {
  const [agentPredictions, setAgentPredictions] = useState<any>({
    meanReversion: { prediction: 0, confidence: 0 },
    momentum: { prediction: 0, confidence: 0 },
    sentimentMomentum: { prediction: 0, confidence: 0 },
  });
  const [finalDecision, setFinalDecision] = useState<{
    action: "buy" | "hold" | "sell";
    confidence: number;
  }>({
    action: "hold",
    confidence: 0,
  });

  const [weights, setWeights] = useState({
    meanReversion: 0.19,
    momentum: 0.35,
    sentimentMomentum: 0.46,
  });

  useEffect(() => {
    if (priceData.length === 0 || sentimentData.length === 0) return;

    // Simulate agent predictions based on the data
    // Mean Reversion Agent
    const recentPrices = priceData.slice(-10).map((d) => d.price);
    const avgPrice =
      recentPrices.reduce((sum, price) => sum + price, 0) / recentPrices.length;
    const currentPrice = recentPrices[recentPrices.length - 1];
    const priceDiff = (currentPrice - avgPrice) / avgPrice;

    // If price is above average, mean reversion predicts a fall (negative)
    // If price is below average, mean reversion predicts a rise (positive)
    const meanReversionPrediction = -priceDiff;
    const meanReversionConfidence = Math.min(0.9, Math.abs(priceDiff) * 5);

    // Momentum Agent
    const priceChange =
      (recentPrices[recentPrices.length - 1] - recentPrices[0]) /
      recentPrices[0];
    const momentumPrediction = priceChange;
    const momentumConfidence = Math.min(0.9, Math.abs(priceChange) * 3);

    // Sentiment Momentum Agent
    const recentSentiments = sentimentData.slice(-10).map((d) => d.sentiment);
    const avgSentiment =
      recentSentiments.reduce((sum, sentiment) => sum + sentiment, 0) /
      recentSentiments.length;
    const sentimentTrend = avgSentiment * 2; // Scale up for effect
    const sentimentConfidence = Math.min(0.9, Math.abs(avgSentiment) * 2);

    setAgentPredictions({
      meanReversion: {
        prediction: meanReversionPrediction,
        confidence: meanReversionConfidence,
      },
      momentum: {
        prediction: momentumPrediction,
        confidence: momentumConfidence,
      },
      sentimentMomentum: {
        prediction: sentimentTrend,
        confidence: sentimentConfidence,
      },
    });

    // Calculate weighted prediction
    const weightedPrediction =
      meanReversionPrediction *
        weights.meanReversion *
        meanReversionConfidence +
      momentumPrediction * weights.momentum * momentumConfidence +
      sentimentTrend * weights.sentimentMomentum * sentimentConfidence;

    const totalConfidenceWeight =
      weights.meanReversion * meanReversionConfidence +
      weights.momentum * momentumConfidence +
      weights.sentimentMomentum * sentimentConfidence;

    const normalizedPrediction = weightedPrediction / totalConfidenceWeight;

    // Determine action based on prediction
    let action: "buy" | "hold" | "sell" = "hold";
    if (normalizedPrediction > 0.02) action = "buy";
    else if (normalizedPrediction < -0.02) action = "sell";

    setFinalDecision({
      action,
      confidence: Math.min(0.95, Math.abs(normalizedPrediction) * 10),
    });
  }, [priceData, sentimentData, weights]);

  const getActionColor = (action: string) => {
    switch (action) {
      case "buy":
        return "text-[#86A5A5]";
      case "sell":
        return "text-[#B35D5D]";
      default:
        return "text-yellow-500";
    }
  };

  const getActionIcon = (action: string) => {
    switch (action) {
      case "buy":
        return <ArrowUpIcon className="h-5 w-5" />;
      case "sell":
        return <ArrowDownIcon className="h-5 w-5" />;
      default:
        return <MinusIcon className="h-5 w-5" />;
    }
  };

  const getPredictionBadge = (prediction: number) => {
    if (prediction > 0.01) return <Badge variant="success">Bullish</Badge>;
    if (prediction < -0.01) return <Badge variant="destructive">Bearish</Badge>;
    return <Badge variant="outline">Neutral</Badge>;
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center">
          <Brain className="mr-2 h-5 w-5" />
          Multi-Agent Decision System
        </CardTitle>
        <CardDescription>
          Analysis and recommendations for {stockSymbol}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="md:col-span-3 grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card>
              <CardHeader className="py-2">
                <CardTitle className="text-sm flex items-center">
                  <LineChart className="mr-2 h-4 w-4" />
                  Mean Regression Agent
                </CardTitle>
              </CardHeader>
              <CardContent className="py-1">
                <div className="flex justify-between items-center mb-2">
                  <div>
                    {getPredictionBadge(
                      agentPredictions.meanReversion.prediction
                    )}
                  </div>
                  <div className="text-sm text-muted-foreground">
                    Weight: {(weights.meanReversion * 100).toFixed(0)}%
                  </div>
                </div>
                <div className="space-y-1">
                  <div className="text-sm">Confidence</div>
                  <Progress
                    value={agentPredictions.meanReversion.confidence * 100}
                  />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="py-2">
                <CardTitle className="text-sm flex items-center">
                  <TrendingUp className="mr-2 h-4 w-4" />
                  Momentum Agent
                </CardTitle>
              </CardHeader>
              <CardContent className="py-1">
                <div className="flex justify-between items-center mb-2">
                  <div>
                    {getPredictionBadge(agentPredictions.momentum.prediction)}
                  </div>
                  <div className="text-sm text-muted-foreground">
                    Weight: {(weights.momentum * 100).toFixed(0)}%
                  </div>
                </div>
                <div className="space-y-1">
                  <div className="text-sm">Confidence</div>
                  <Progress
                    value={agentPredictions.momentum.confidence * 100}
                  />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="py-2">
                <CardTitle className="text-sm flex items-center">
                  <BarChart3 className="mr-2 h-4 w-4" />
                  Sentiment Momentum
                </CardTitle>
              </CardHeader>
              <CardContent className="py-1">
                <div className="flex justify-between items-center mb-2">
                  <div>
                    {getPredictionBadge(
                      agentPredictions.sentimentMomentum.prediction
                    )}
                  </div>
                  <div className="text-sm text-muted-foreground">
                    Weight: {(weights.sentimentMomentum * 100).toFixed(0)}%
                  </div>
                </div>
                <div className="space-y-1">
                  <div className="text-sm">Confidence</div>
                  <Progress
                    value={agentPredictions.sentimentMomentum.confidence * 100}
                  />
                </div>
              </CardContent>
            </Card>
          </div>

          <Card className="bg-muted/50">
            <CardHeader className="py-4">
              <CardTitle className="text-sm text-center">
                Final Decision
              </CardTitle>
            </CardHeader>
            <CardContent className="py-2">
              <div className="flex flex-col items-center justify-center">
                <div
                  className={`text-sm font-bold uppercase ${getActionColor(
                    finalDecision.action
                  )} flex items-center`}
                >
                  {getActionIcon(finalDecision.action)}
                  {finalDecision.action}
                </div>
                <div className="mt-4 w-full space-y-1">
                  <div className="text-sm text-center">
                    Confidence {(finalDecision.confidence * 100).toFixed(0)}%
                  </div>
                  <Progress
                    value={finalDecision.confidence * 100}
                    className="h-3"
                  />
                  {/* <div className="text-sm text-center text-muted-foreground">
                    {(finalDecision.confidence * 100).toFixed(0)}%
                  </div> */}
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </CardContent>
    </Card>
  );
}
