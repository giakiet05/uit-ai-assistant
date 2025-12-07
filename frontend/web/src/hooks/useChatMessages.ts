import { useState, useEffect } from "react"
import { apiClient } from "@/lib/api"
import type { ChatMessageResponse } from "@/lib/api"
import { toast } from "sonner"

export function useChatMessages(sessionId: string | null, limit?: number) {
  const [messages, setMessages] = useState<ChatMessageResponse[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchMessages = async () => {
    if (!sessionId) {
      setMessages([])
      return
    }

    try {
      setLoading(true)
      setError(null)
      const response = await apiClient.getChatMessages(sessionId, limit)
      if (response.success && response.data) {
        setMessages(response.data)
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Failed to fetch messages"
      setError(errorMessage)
      toast.error(errorMessage)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchMessages()
  }, [sessionId, limit])

  const addMessage = (message: ChatMessageResponse) => {
    setMessages((prev) => [...prev, message])
  }

  const clearMessages = () => {
    setMessages([])
  }

  return {
    messages,
    loading,
    error,
    refetch: fetchMessages,
    addMessage,
    clearMessages,
    setMessages,
  }
}
