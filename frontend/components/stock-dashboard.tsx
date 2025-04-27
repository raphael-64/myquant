"use client";

import { useState, useEffect } from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  getHistoricalData,
  Plus,
  Trash2,
  getSentimentData,
} from "lucide-react";
import { useToast } from "@/hooks/use-toast";

import StockDashboard from "@/components/stock-dashboard";
import AgentWeightsChart from "@/components/agent-weights-chart";
import AgentPerformanceChart from "@/components/agent-performance-chart";
import { addStock, removeStock } from "@/lib/actions";

export default function Home() {
  const [data, setData] = useState(null);
  const [stocks, setStocks] = useState<{ ticker: string; name?: string }[]>([]);
  const [newStock, setNewStock] = useState("");
  const [activeStock, setActiveStock] = useState<string | null>(null);
  const { toast } = useToast();

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setError(null);

      try {
        const marketData = await getMarketData(stockSymbol);

        // Split into priceData and sentimentData
        const formattedPriceData = marketData.map((item: any) => ({
          date: item.timestamp.split("T")[0],
          price: item.price,
          volume: item.volume,
        }));

        const formattedSentimentData = marketData.map((item: any) => ({
          date: item.timestamp.split("T")[0],
          sentiment: item.sentiment_score ?? 0, // fallback to 0 if null
          articles: Math.floor(Math.random() * 50) + 5, // no articles count in db, so fake it
        }));

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
    <main className="container mx-auto py-3">
      <h1 className="text-2xl font-bold mb-3">MyQuant</h1>
      <h2 className="text-2xl font-bold mb-3">
        Self-Evolving Multi-Agent Trading Platform
      </h2>

      <div className="flex items-center space-x-4 mb-4 bg-muted/30 p-2 rounded-lg">
        <div className="flex-grow flex space-x-2">
          <Input
            placeholder="Add stock ticker (e.g., AAPL, TSLA)"
            value={newStock}
            onChange={(e) => setNewStock(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleAddStock()}
            className="h-9"
            list="all-stocks"
          />
          <Button onClick={handleAddStock} size="sm" className="h-9">
            <Plus className="mr-1 h-4 w-4" /> Add
          </Button>
        </div>

        <div className="flex items-center space-x-3 px-3 border-l border-border">
          <div className="text-xs">
            <span className="font-medium">Market Research:</span> 2 agents
          </div>
          <div className="text-xs">
            <span className="font-medium">Analysis:</span> 3 agents
          </div>
          <div className="text-xs">
            <span className="font-medium">Self-learning:</span> Active
          </div>
        </div>
      </div>

      <div className="flex flex-wrap gap-2 mb-4">
        {stocks.map((stock) => (
          <div
            key={stock.ticker}
            onClick={() => setActiveStock(stock.ticker)}
            className="flex items-center bg-muted rounded-md px-3 py-1 cursor-pointer"
          >
            <span className="font-medium mr-2">{stock.name}</span>
            <Button
              variant="ghost"
              size="icon"
              className="h-6 w-6"
              onClick={(e) => {
                e.stopPropagation(); // stop triggering setActiveStock when clicking trash
                handleRemoveStock(stock.ticker);
              }}
            >
              <Trash2 className="h-4 w-4" />
            </Button>
          </div>
        ))}
      </div>

      {activeStock ? (
        <>
          <Tabs defaultValue="dashboard" className="w-full">
            <TabsList className="grid w-full grid-cols-3 h-9">
              <TabsTrigger value="dashboard" className="text-xs">
                Stock Dashboard
              </TabsTrigger>
              <TabsTrigger value="weights" className="text-xs">
                Agent Weights
              </TabsTrigger>
              <TabsTrigger value="performance" className="text-xs">
                Agent Performance
              </TabsTrigger>
            </TabsList>

            <TabsContent value="dashboard">
              <div className="mb-2">
                <div className="flex space-x-1 overflow-x-auto py-1">
                  {/* {stocks.map((stock) => (
                    <Button
                      key={stock}
                      variant={activeStock === stock ? "default" : "outline"}
                      onClick={() => setActiveStock(stock)}
                      size="sm"
                      className="h-7 px-2 py-0"
                    >
                      {stock}
                    </Button>
                  ))} */}
                  {/* <div>
                    {stocks.map((stock) => (
                      <Button key={stock}>{stock}</Button>
                    ))}
                  </div> */}
                </div>
              </div>

              <StockDashboard stockSymbol={activeStock} />
            </TabsContent>

            <TabsContent value="weights">
              <AgentWeightsChart stockSymbol={activeStock} />
            </TabsContent>

            <TabsContent value="performance">
              <AgentPerformanceChart stockSymbol={activeStock} />
            </TabsContent>
          </Tabs>
        </>
      ) : (
        <Card>
          <CardContent className="pt-6">
            <div className="text-center py-10">
              <h3 className="text-lg font-medium mb-2">No Stocks Added</h3>
              <p className="text-muted-foreground mb-4">
                Add stocks above to start tracking and analyzing them with the
                multi-agent system.
              </p>
            </div>
          </CardContent>
        </Card>
      )}
    </main>
  );
}
