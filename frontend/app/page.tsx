"use client";

import { useState, useEffect } from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Plus, Trash2 } from "lucide-react";
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
    // Load saved stocks from localStorage
    fetch("http://localhost:8000/assets")
      .then((res) => res.json())
      .then((json) => {
        setStocks(json);
        setActiveStock(json[0].ticker);
      });
  }, []);
  const handleAddStock = async () => {
    if (!newStock) return;

    const ticker = newStock.toUpperCase().trim();

    if (stocks.map((stock) => stock.ticker).includes(ticker)) {
      toast({
        title: "Stock already added",
        description: `${ticker} is already in your watchlist.`,
        variant: "destructive",
      });
      return;
    }

    try {
      // ✅ POST the new stock to the database
      const res = await fetch("http://localhost:8000/assets", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          ticker: ticker,
          // name: ticker, // or leave empty / customize name later
          asset_type: "stock", // assuming "stock" is the default
        }),
      });

      if (!res.ok) {
        throw new Error("Failed to add stock");
      }

      const newAsset = await res.json(); // { ticker, name, asset_type }

      // ✅ Update your frontend stocks state properly
      const updatedStocks = [
        ...stocks,
        { ticker: newAsset.ticker, name: newAsset.name },
      ];
      setStocks(updatedStocks);

      localStorage.setItem("trackedStocks", JSON.stringify(updatedStocks));

      if (!activeStock) {
        setActiveStock(newAsset.ticker);
      }

      setNewStock("");

      toast({
        title: "Stock added",
        description: `${newAsset.ticker} has been added to your watchlist.`,
      });
    } catch (error) {
      console.error(error);
      toast({
        title: "Error adding stock",
        description: "Please check the ticker symbol and try again.",
        variant: "destructive",
      });
    }
  };

  const handleRemoveStock = async (ticker: string) => {
    try {
      await removeStock(ticker);

      const updatedStocks = stocks.filter((stock) => stock.ticker !== ticker);
      setStocks(updatedStocks);
      localStorage.setItem("trackedStocks", JSON.stringify(updatedStocks));

      if (activeStock === ticker) {
        setActiveStock(
          updatedStocks.length > 0
            ? typeof updatedStocks[0] === "string"
              ? updatedStocks[0]
              : updatedStocks[0].ticker
            : null
        );
      }

      toast({
        title: "Stock removed",
        description: `${ticker} has been removed from your watchlist.`,
      });
    } catch (error) {
      toast({
        title: "Error removing stock",
        description: "An error occurred while removing the stock.",
        variant: "destructive",
      });
    }
  };

  // void changeActiveStock();

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
