"use client"

import { useState, useEffect, useRef } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Sector,
} from "recharts"
import { Brain, History, PieChartIcon } from "lucide-react"

interface AgentWeightsChartProps {
  stockSymbol: string
}

export default function AgentWeightsChart({ stockSymbol }: AgentWeightsChartProps) {
  const [weightHistory, setWeightHistory] = useState<any[]>([])
  const [currentWeights, setCurrentWeights] = useState([
    { name: "Mean Reversion", value: 0.33, color: "hsl(var(--chart-1))" },
    { name: "Momentum", value: 0.33, color: "hsl(var(--chart-2))" },
    { name: "Sentiment Momentum", value: 0.34, color: "hsl(var(--chart-3))" },
  ])
  const [activeIndex, setActiveIndex] = useState(0)
  const intervalRef = useRef<NodeJS.Timeout | null>(null)

  // Generate initial weight history data
  useEffect(() => {
    if (!stockSymbol) return

    // Generate mock weight history data
    const mockData = Array.from({ length: 30 }, (_, i) => {
      const date = new Date()
      date.setDate(date.getDate() - (30 - i))

      // Start with equal weights and gradually adjust based on performance
      const baseWeight = 0.33
      const dayFactor = i / 30

      // Simulate weights changing over time
      // For this demo, we'll make mean reversion gradually lose weight
      // while sentiment momentum gains weight
      return {
        date: date.toISOString().split("T")[0],
        meanReversion: Math.max(0.1, baseWeight - dayFactor * 0.15),
        momentum: baseWeight,
        sentimentMomentum: Math.min(0.6, baseWeight + dayFactor * 0.15),
      }
    })

    setWeightHistory(mockData)

    // Set initial weights from the last data point
    if (mockData.length > 0) {
      const lastData = mockData[mockData.length - 1]
      setCurrentWeights([
        { name: "Mean Reversion", value: lastData.meanReversion, color: "hsl(var(--chart-1))" },
        { name: "Momentum", value: lastData.momentum, color: "hsl(var(--chart-2))" },
        { name: "Sentiment Momentum", value: lastData.sentimentMomentum, color: "hsl(var(--chart-3))" },
      ])
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
      }
    }
  }, [stockSymbol])

  // Set up interval to update weights periodically
  useEffect(() => {
    if (!stockSymbol) return

    // Start the simulation of weight changes
    intervalRef.current = setInterval(() => {
      setCurrentWeights((prevWeights) => {
        // Create a copy of the weights
        const newWeights = [...prevWeights]

        // Randomly adjust weights slightly
        const adjustmentFactor = 0.01
        let meanReversionChange = (Math.random() - 0.5) * adjustmentFactor
        let momentumChange = (Math.random() - 0.5) * adjustmentFactor
        let sentimentChange = (Math.random() - 0.5) * adjustmentFactor

        // Ensure the total remains 1.0
        const totalChange = meanReversionChange + momentumChange + sentimentChange
        meanReversionChange -= totalChange / 3
        momentumChange -= totalChange / 3
        sentimentChange -= totalChange / 3

        // Apply changes with constraints
        newWeights[0].value = Math.max(0.1, Math.min(0.6, newWeights[0].value + meanReversionChange))
        newWeights[1].value = Math.max(0.1, Math.min(0.6, newWeights[1].value + momentumChange))
        newWeights[2].value = Math.max(0.1, Math.min(0.6, newWeights[2].value + sentimentChange))

        // Normalize to ensure sum is exactly 1.0
        const sum = newWeights[0].value + newWeights[1].value + newWeights[2].value
        newWeights[0].value = newWeights[0].value / sum
        newWeights[1].value = newWeights[1].value / sum
        newWeights[2].value = newWeights[2].value / sum

        return newWeights
      })
    }, 2000) // Update every 2 seconds

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
      }
    }
  }, [stockSymbol])

  // Custom active shape for the pie chart
  const renderActiveShape = (props: any) => {
    const { cx, cy, innerRadius, outerRadius, startAngle, endAngle, fill, payload, percent, value } = props

    return (
      <g>
        <text x={cx} y={cy - 20} dy={8} textAnchor="middle" fill="hsl(var(--foreground))">
          {payload.name}
        </text>
        <text x={cx} y={cy + 10} dy={8} textAnchor="middle" fill="hsl(var(--foreground))">
          {`${(value * 100).toFixed(1)}%`}
        </text>
        <Sector
          cx={cx}
          cy={cy}
          innerRadius={innerRadius}
          outerRadius={outerRadius + 10}
          startAngle={startAngle}
          endAngle={endAngle}
          fill={fill}
        />
        <Sector
          cx={cx}
          cy={cy}
          startAngle={startAngle}
          endAngle={endAngle}
          innerRadius={outerRadius + 10}
          outerRadius={outerRadius + 15}
          fill={fill}
        />
      </g>
    )
  }

  const onPieEnter = (_: any, index: number) => {
    setActiveIndex(index)
  }

  return (
    <div className="grid gap-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Brain className="mr-2 h-5 w-5" />
            Agent Weight Evolution
          </CardTitle>
          <CardDescription>Self-learning system weight adjustments for {stockSymbol}</CardDescription>
        </CardHeader>
        <CardContent>
          <Tabs defaultValue="pie">
            <TabsList className="mb-4">
              <TabsTrigger value="pie">
                <PieChartIcon className="mr-2 h-4 w-4" />
                Live Weights
              </TabsTrigger>
              <TabsTrigger value="line">Line Chart</TabsTrigger>
            </TabsList>

            <TabsContent value="pie">
              <div className="h-[300px] flex flex-col items-center justify-center">
                <h3 className="text-base font-medium mb-2">Current Agent Weights</h3>
                <ResponsiveContainer width="100%" height={220}>
                  <PieChart>
                    <Pie
                      activeIndex={activeIndex}
                      activeShape={renderActiveShape}
                      data={currentWeights}
                      cx="50%"
                      cy="50%"
                      innerRadius={80}
                      outerRadius={120}
                      fill="#8884d8"
                      dataKey="value"
                      onMouseEnter={onPieEnter}
                      isAnimationActive={true}
                      animationBegin={0}
                      animationDuration={500}
                    >
                      {currentWeights.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip formatter={(value: any) => [`${(value * 100).toFixed(1)}%`, ""]} />
                  </PieChart>
                </ResponsiveContainer>
                <div className="flex justify-center space-x-6 mt-4">
                  {currentWeights.map((entry, index) => (
                    <div key={`legend-${index}`} className="flex items-center">
                      <div className="w-3 h-3 mr-2 rounded-full" style={{ backgroundColor: entry.color }} />
                      <span className="text-sm">
                        {entry.name}: {(entry.value * 100).toFixed(1)}%
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </TabsContent>

            <TabsContent value="line">
              <div className="h-[300px]">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={weightHistory}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis
                      dataKey="date"
                      tickFormatter={(value) => {
                        const date = new Date(value)
                        return `${date.getMonth() + 1}/${date.getDate()}`
                      }}
                    />
                    <YAxis domain={[0, 1]} />
                    <Tooltip
                      formatter={(value: any) => [`${(value * 100).toFixed(0)}%`, ""]}
                      labelFormatter={(label) => {
                        const date = new Date(label)
                        return date.toLocaleDateString()
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
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </TabsContent>
          </Tabs>

          <div className="mt-6">
            <div className="flex items-center mb-2">
              <History className="mr-2 h-4 w-4" />
              <h3 className="text-sm font-medium">Weight Adjustment Process</h3>
            </div>
            <p className="text-sm text-muted-foreground">
              The system automatically adjusts agent weights based on prediction accuracy. When an agent consistently
              makes accurate predictions, its weight increases. Conversely, when an agent's predictions are less
              accurate, its weight decreases. Watch the pie chart to see these adjustments happen in real-time.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
