import { useState, useEffect } from "react"
import { apiClient } from "@/lib/api"
import type { UserSettings, UpdateSettingsRequest } from "@/lib/api"
import { toast } from "sonner"

export function useSettings() {
  const [settings, setSettings] = useState<UserSettings | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchSettings = async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await apiClient.getSettings()
      if (response.success) {
        setSettings(response.data)
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Failed to fetch settings"
      setError(errorMessage)
      toast.error(errorMessage)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchSettings()
  }, [])

  return {
    settings,
    loading,
    error,
    refetch: fetchSettings,
  }
}

export function useUpdateSettings() {
  const [loading, setLoading] = useState(false)

  const updateSettings = async (data: UpdateSettingsRequest) => {
    console.log("🔧 useUpdateSettings - Request data:", data)
    try {
      setLoading(true)
      const response = await apiClient.updateSettings(data)
      console.log("✅ useUpdateSettings - Response:", response)
      if (response.success) {
        toast.success("Settings updated successfully")
        return response.data
      }
    } catch (err) {
      console.error("❌ useUpdateSettings - Error:", err)
      const errorMessage = err instanceof Error ? err.message : "Failed to update settings"
      toast.error(errorMessage)
      throw err
    } finally {
      setLoading(false)
    }
  }

  return {
    updateSettings,
    loading,
  }
}
