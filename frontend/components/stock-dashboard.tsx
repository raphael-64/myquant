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
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { ArrowUpIcon, ArrowDownIcon, Newspaper } from "lucide-react";
import { getHistoricalData, getMarketData, getSentimentData } from "@/lib/actions";
import { useToast } from "@/hooks/use-toast";
import AgentDecision from "@/components/agent-decision";

interface StockDashboardProps {
  stockSymbol: string;
}

export default function StockDashboard({ stockSymbol }: StockDashboardProps) {
  const [priceData, setPriceData] = useState<any[]>([]);
  const [sentimentData, setSentimentData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { toast } = useToast();

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setError(null);

      try {
        const marketData = await getMarketData(stockSymbol);
        const historicalData = await getHistoricalData(stockSymbol);
        const sentimentData = await getSentimentData(stockSymbol);
        console.log(sentimentData);
        
        // Split into priceData and sentimentData
        const formattedPriceData = historicalData.map((item: any) => ({
          date: item.Date,
          price: item.Close,
          volume: item.Volume,
        }));

        const formattedSentimentData = sentimentData.map((item: any, index) => {
          // Generate a random date in the last 30 days
          const today = new Date();
          const randomDaysAgo = Math.floor(Math.random() * 30);
          const randomDate = new Date(today);
          randomDate.setDate(today.getDate() - randomDaysAgo);
          
          // Format as YYYY-MM-DD
          const formattedDate = randomDate.toISOString().split('T')[0];
          
          return {
            date: formattedDate,
            sentiment: item.sentiment_score ?? 0,
            articles: Math.floor(Math.random() * 50) + 5,
          };
        });

        setPriceData(formattedPriceData);
        setSentimentData(formattedSentimentData);
      } catch (err) {
        setError("Failed to fetch stock data");
        toast({
          title: "Error fetching data",
          description: "Could not load stock data. Please try again later.",
          variant: "destructive",
        });
      } finally {
        setLoading(false);
      }
    };

    if (stockSymbol) {
      fetchData();
    }
  }, [stockSymbol, toast]);

  // Generate mock data for demonstration
  useEffect(() => {
    if (!stockSymbol) return;

    // Mock price data if API call failed or for demo purposes
    if (priceData.length === 0) {
      const mockPriceData = Array.from({ length: 30 }, (_, i) => {
        const date = new Date();
        date.setDate(date.getDate() - (30 - i));

        return {
          date: date.toISOString().split("T")[0],
          price:
            100 + Math.random() * 50 + i * (Math.random() > 0.5 ? 1 : -0.5),
          volume: Math.floor(Math.random() * 10000000) + 1000000,
        };
      });
      setPriceData(mockPriceData);
    }

    // Mock sentiment data
    if (sentimentData.length === 0) {
      const mockSentimentData = Array.from({ length: 30 }, (_, i) => {
        const date = new Date();
        date.setDate(date.getDate() - (30 - i));

        return {
          date: date.toISOString().split("T")[0],
          sentiment: Math.random() * 2 - 1, // -1 to 1
          articles: Math.floor(Math.random() * 50) + 5,
        };
      });
      setSentimentData(mockSentimentData);
    }
  }, [stockSymbol, priceData.length, sentimentData.length]);

  const currentPrice =
    priceData.length > 0 ? priceData[priceData.length - 1].price : 0;
  const previousPrice =
    priceData.length > 1 ? priceData[priceData.length - 2].price : 0;
  const priceChange = currentPrice - previousPrice;
  const priceChangePercent = previousPrice
    ? (priceChange / previousPrice) * 100
    : 0;

  const currentSentiment =
    sentimentData.length > 0
      ? sentimentData[sentimentData.length - 1].sentiment
      : 0;

  const formatPrice = (price: number) => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
    }).format(price);
  };

  return (
    <div className="grid gap-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-2xl">{stockSymbol}</CardTitle>
            <CardDescription>Price and Volume Analysis</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-baseline justify-between">
              <div className="text-3xl font-bold">
                {formatPrice(currentPrice)}
              </div>
              <div
                className={`flex items-center ${
                  priceChange >= 0 ? "text-green-500" : "text-red-500"
                }`}
              >
                {priceChange >= 0 ? (
                  <ArrowUpIcon className="mr-1 h-4 w-4" />
                ) : (
                  <ArrowDownIcon className="mr-1 h-4 w-4" />
                )}
                <span className="font-medium">
                  {priceChange.toFixed(2)} ({priceChangePercent.toFixed(2)}%)
                </span>
              </div>
            </div>

            <div className="h-[160px] mt-2">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={priceData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis
                    dataKey="date"
                    tickFormatter={(value) => {
                      const date = new Date(value);
                      return `${date.getMonth() + 1}/${date.getDate()}`;
                    }}
                  />
                  <YAxis domain={["auto", "auto"]} />
                  <Tooltip
                    formatter={(value: any) => [formatPrice(value), "Price"]}
                    labelFormatter={(label) => {
                      const date = new Date(label);
                      return date.toLocaleDateString();
                    }}
                  />
                  <Line
                    type="monotone"
                    dataKey="price"
                    stroke="hsl(var(--primary))"
                    strokeWidth={2}
                    dot={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center">
              <Newspaper className="mr-2 h-5 w-5" />
              Market Sentiment
            </CardTitle>
            <CardDescription>
              Research agents for news/social media
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between mb-4">
              <div>
                <div className="text-sm text-muted-foreground">
                  Current Sentiment
                </div>
                <div className="flex items-center mt-1">
                  <Badge
                    variant={
                      currentSentiment > 0.3
                        ? "success"
                        : currentSentiment < -0.3
                        ? "destructive"
                        : "outline"
                    }
                  >
                    {currentSentiment > 0.3
                      ? "Positive"
                      : currentSentiment < -0.3
                      ? "Negative"
                      : "Neutral"}
                  </Badge>
                  <span className="ml-2 text-sm">
                    {(currentSentiment * 100).toFixed(1)}%
                  </span>
                </div>
              </div>
              <div>
                <div className="text-sm text-muted-foreground">
                  Articles Analyzed
                </div>
                <div className="text-xl font-medium mt-1">
                  {sentimentData.length > 0
                    ? sentimentData[sentimentData.length - 1].articles
                    : 0}
                </div>
              </div>
            </div>

            <div className="h-[160px]">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={sentimentData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis
                    dataKey="date"
                    tickFormatter={(value) => {
                      const date = new Date(value);
                      return `${date.getMonth() + 1}/${date.getDate()}`;
                    }}
                  />
                  <YAxis domain={[-1, 1]} />
                  <Tooltip
                    formatter={(value: any) => [
                      `${(value * 100).toFixed(1)}%`,
                      "Sentiment",
                    ]}
                    labelFormatter={(label) => {
                      const date = new Date(label);
                      return date.toLocaleDateString();
                    }}
                  />
                  <Line
                    type="monotone"
                    dataKey="sentiment"
                    stroke="hsl(var(--primary))"
                    strokeWidth={2}
                    dot={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      </div>

      <AgentDecision
        stockSymbol={stockSymbol}
        priceData={priceData}
        sentimentData={sentimentData}
      />
    </div>
  );
}
