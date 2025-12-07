import { useState } from "react"
import { apiClient } from "@/lib/api"
import type { ChatRequest, ChatResponse } from "@/lib/api"
import { toast } from "sonner"

export function useSendMessage() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const sendMessage = async (data: ChatRequest): Promise<ChatResponse | null> => {
    setLoading(true)
    setError(null)

    try {
      const response = await apiClient.sendChatMessage(data)
      if (response.success && response.data) {
        return response.data
      }

      const errorMsg = response.message || "Failed to send message"
      setError(errorMsg)
      toast.error(errorMsg)
      return null
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Failed to send message"
      setError(errorMessage)
      toast.error(errorMessage)
      return null
    } finally {
      setLoading(false)
    }
  }

  return {
    sendMessage,
    loading,
    error,
  }
}
