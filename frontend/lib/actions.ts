"use server"

// This file contains server actions for fetching stock data and managing user stocks

export async function getStockData(symbol: string) {
  // In a real application, this would fetch data from a financial API
  // For demo purposes, we'll return mock data

  try {
    // Simulate API call delay
    await new Promise((resolve) => setTimeout(resolve, 500))

    // Generate mock price data
    const data = Array.from({ length: 30 }, (_, i) => {
      const date = new Date()
      date.setDate(date.getDate() - (30 - i))

      return {
        date: date.toISOString().split("T")[0],
        price: 100 + Math.random() * 50 + i * (Math.random() > 0.5 ? 1 : -0.5),
        volume: Math.floor(Math.random() * 10000000) + 1000000,
      }
    })

    return { success: true, data }
  } catch (error) {
    console.error("Error fetching stock data:", error)
    return { success: false, error: "Failed to fetch stock data" }
  }
}

export async function getStockSentiment(symbol: string) {
  // In a real application, this would fetch sentiment data from a news API or social media
  // For demo purposes, we'll return mock data

  try {
    // Simulate API call delay
    await new Promise((resolve) => setTimeout(resolve, 700))

    // Generate mock sentiment data
    const data = Array.from({ length: 30 }, (_, i) => {
      const date = new Date()
      date.setDate(date.getDate() - (30 - i))

      return {
        date: date.toISOString().split("T")[0],
        sentiment: Math.random() * 2 - 1, // -1 to 1
        articles: Math.floor(Math.random() * 50) + 5,
      }
    })

    return { success: true, data }
  } catch (error) {
    console.error("Error fetching sentiment data:", error)
    return { success: false, error: "Failed to fetch sentiment data" }
  }
}

export async function addStock(symbol: string) {
  // In a real application, this would validate the stock symbol against a financial API
  // and add it to the user's database record

  try {
    // Simulate API call delay
    await new Promise((resolve) => setTimeout(resolve, 300))

    // For demo purposes, we'll just return success
    // In a real app, you would validate the symbol exists
    return { success: true }
  } catch (error) {
    console.error("Error adding stock:", error)
    throw new Error("Failed to add stock")
  }
}

export async function removeStock(symbol: string) {
  // In a real application, this would remove the stock from the user's database record

  try {
    // Simulate API call delay
    await new Promise((resolve) => setTimeout(resolve, 200))

    // For demo purposes, we'll just return success
    return { success: true }
  } catch (error) {
    console.error("Error removing stock:", error)
    throw new Error("Failed to remove stock")
  }
}
