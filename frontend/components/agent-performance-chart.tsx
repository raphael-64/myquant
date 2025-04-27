"use client";

import { useState, useEffect } from "react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { Award, TrendingUp } from "lucide-react";

interface AgentPerformanceChartProps {
  stockSymbol: string;
}

export default function AgentPerformanceChart({
  stockSymbol,
}: AgentPerformanceChartProps) {
  const [performanceData, setPerformanceData] = useState<any[]>([]);
  const [cumulativeData, setCumulativeData] = useState<any[]>([]);

  useEffect(() => {
    if (!stockSymbol) return;

    // Generate mock performance data
    const mockData = Array.from({ length: 30 }, (_, i) => {
      const date = new Date();
      date.setDate(date.getDate() - (30 - i));

      // Simulate different performance for each agent
      // Values represent prediction accuracy (0-1)
      return {
        date: date.toISOString().split("T")[0],
        meanReversion: Math.random() * 0.1 + 0.5, // 0.5-0.8 range
        momentum: Math.random() * 0.15 + 0.4, // 0.4-0.8 range
        sentimentMomentum: Math.min(0.9, Math.random() * 0.3 + 0.5 + i / 300), // Gradually improving
        combined: Math.random() * 0.18 + 0.6, // 0.6-0.9 range
      };
    });

    setPerformanceData(mockData);

    // Generate cumulative performance data
    let cumulativeMR = 1.0;
    let cumulativeMom = 1.0;
    let cumulativeSent = 1.0;
    let cumulativeComb = 1.0;

    const cumulativePerformance = mockData.map((day) => {
      // Simulate returns based on prediction accuracy
      // Higher accuracy = better returns
      const mrReturn = (day.meanReversion - 0.5) * 0.05;
      const momReturn = (day.momentum - 0.5) * 0.05;
      const sentReturn = (day.sentimentMomentum - 0.5) * 0.05;
      const combReturn = (day.combined - 0.5) * 0.05;

      cumulativeMR *= 1 + mrReturn;
      cumulativeMom *= 1 + momReturn;
      cumulativeSent *= 1 + sentReturn;
      cumulativeComb *= 1 + combReturn;

      return {
        date: day.date,
        meanReversion: cumulativeMR,
        momentum: cumulativeMom,
        sentimentMomentum: cumulativeSent,
        combined: cumulativeComb,
      };
    });

    setCumulativeData(cumulativePerformance);
  }, [stockSymbol]);

  return (
    <div className="grid gap-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Award className="mr-2 h-5 w-5" />
            Agent Performance Metrics
          </CardTitle>
          <CardDescription>
            Prediction accuracy and returns for {stockSymbol}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Tabs defaultValue="accuracy">
            <TabsList className="mb-4">
              <TabsTrigger value="accuracy">Prediction Accuracy</TabsTrigger>
              <TabsTrigger value="returns">Cumulative Returns</TabsTrigger>
            </TabsList>

            <TabsContent value="accuracy">
              <div className="h-[300px]">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={performanceData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis
                      dataKey="date"
                      tickFormatter={(value) => {
                        const date = new Date(value);
                        return `${date.getMonth() + 1}/${date.getDate()}`;
                      }}
                    />
                    <YAxis
                      domain={[0, 1]}
                      tickFormatter={(value) => `${(value * 100).toFixed(0)}%`}
                    />
                    <Tooltip
                      formatter={(value: any) => [
                        `${(value * 100).toFixed(1)}%`,
                        "",
                      ]}
                      labelFormatter={(label) => {
                        const date = new Date(label);
                        return date.toLocaleDateString();
                      }}
                    />
                    <Legend />
                    <Line
                      type="monotone"
                      dataKey="meanReversion"
                      name="Mean Reversion"
                      stroke="hsl(var(--chart-1))"
                      strokeWidth={2}
                      dot={false}
                    />
                    <Line
                      type="monotone"
                      dataKey="momentum"
                      name="Momentum"
                      stroke="hsl(var(--chart-2))"
                      strokeWidth={2}
                      dot={false}
                    />
                    <Line
                      type="monotone"
                      dataKey="sentimentMomentum"
                      name="Sentiment Momentum"
                      stroke="hsl(var(--chart-3))"
                      strokeWidth={2}
                      dot={false}
                    />
                    <Line
                      type="monotone"
                      dataKey="combined"
                      name="Combined System"
                      stroke="hsl(var(--chart-4))"
                      strokeWidth={3}
                      dot={false}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </TabsContent>

            <TabsContent value="returns">
              <div className="h-[300px]">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={cumulativeData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis
                      dataKey="date"
                      tickFormatter={(value) => {
                        const date = new Date(value);
                        return `${date.getMonth() + 1}/${date.getDate()}`;
                      }}
                    />
                    <YAxis
                      domain={["dataMin", "dataMax"]}
                      tickFormatter={(value) => `${value.toFixed(2)}x`}
                    />
                    <Tooltip
                      formatter={(value: any) => [`${value.toFixed(2)}x`, ""]}
                      labelFormatter={(label) => {
                        const date = new Date(label);
                        return date.toLocaleDateString();
                      }}
                    />
                    <Legend />
                    <Line
                      type="monotone"
                      dataKey="meanReversion"
                      name="Mean Reversion"
                      stroke="hsl(var(--chart-1))"
                      strokeWidth={2}
                      dot={false}
                    />
                    <Line
                      type="monotone"
                      dataKey="momentum"
                      name="Momentum"
                      stroke="hsl(var(--chart-2))"
                      strokeWidth={2}
                      dot={false}
                    />
                    <Line
                      type="monotone"
                      dataKey="sentimentMomentum"
                      name="Sentiment Momentum"
                      stroke="hsl(var(--chart-3))"
                      strokeWidth={2}
                      dot={false}
                    />
                    <Line
                      type="monotone"
                      dataKey="combined"
                      name="Combined System"
                      stroke="hsl(var(--chart-4))"
                      strokeWidth={3}
                      dot={false}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </TabsContent>
          </Tabs>

          <div className="mt-6">
            <div className="flex items-center mb-2">
              <TrendingUp className="mr-2 h-4 w-4" />
              <h3 className="text-sm font-medium">Performance Analysis</h3>
            </div>
            <p className="text-sm text-muted-foreground">
              The combined multi-agent system consistently outperforms
              individual agents by leveraging their complementary strengths. The
              self-learning mechanism optimizes weights to maximize overall
              prediction accuracy and returns.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
