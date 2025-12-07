import { useState, useEffect } from "react"
import { apiClient } from "@/lib/api"
import type { ChatSession, GetSessionsQuery } from "@/lib/api"
import { toast } from "sonner"

export function useChatSessions(query?: GetSessionsQuery) {
  const [sessions, setSessions] = useState<ChatSession[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchSessions = async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await apiClient.getChatSessions(query)
      if (response.success && response.data) {
        setSessions(response.data)
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Failed to fetch sessions"
      setError(errorMessage)
      toast.error(errorMessage)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchSessions()
  }, [query?.page, query?.page_size])

  return {
    sessions,
    loading,
    error,
    refetch: fetchSessions,
  }
}

export function useDeleteSession() {
  const [loading, setLoading] = useState(false)

  const deleteSession = async (sessionId: string): Promise<boolean> => {
    try {
      setLoading(true)
      const response = await apiClient.deleteChatSession(sessionId)
      if (response.success) {
        toast.success("Session deleted successfully")
        return true
      }

      toast.error(response.message || "Failed to delete session")
      return false
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Failed to delete session"
      toast.error(errorMessage)
      return false
    } finally {
      setLoading(false)
    }
  }

  return {
    deleteSession,
    loading,
  }
}

export function useUpdateSessionTitle() {
  const [loading, setLoading] = useState(false)

  const updateTitle = async (sessionId: string, title: string): Promise<ChatSession | null> => {
    try {
      setLoading(true)
      const response = await apiClient.updateSessionTitle(sessionId, { title })
      if (response.success && response.data) {
        toast.success("Session title updated")
        return response.data
      }

      toast.error(response.message || "Failed to update title")
      return null
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Failed to update title"
      toast.error(errorMessage)
      return null
    } finally {
      setLoading(false)
    }
  }

  return {
    updateTitle,
    loading,
  }
}
