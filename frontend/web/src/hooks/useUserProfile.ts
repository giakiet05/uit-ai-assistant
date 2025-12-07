import { useState, useEffect } from "react"
import { apiClient } from "@/lib/api"
import type { User, UpdateProfileRequest } from "@/lib/api"
import { toast } from "sonner"

export function useUserProfile() {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchProfile = async () => {
    console.log("🔄 Fetching user profile...")
    try {
      setLoading(true)
      setError(null)
      const response = await apiClient.getUserProfile()
      console.log("✅ Profile fetched:", response.data)
      if (response.success) {
        setUser(response.data)
        console.log("📸 Avatar URL:", response.data.avatar?.url || "none")
      }
    } catch (err) {
      console.error("❌ Fetch profile error:", err)
      const errorMessage = err instanceof Error ? err.message : "Failed to fetch profile"
      setError(errorMessage)
      toast.error(errorMessage)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchProfile()
  }, [])

  return {
    user,
    loading,
    error,
    refetch: fetchProfile,
  }
}

export function useUpdateProfile() {
  const [loading, setLoading] = useState(false)

  const updateProfile = async (data: UpdateProfileRequest) => {
    try {
      setLoading(true)
      const response = await apiClient.updateUserProfile(data)
      if (response.success) {
        toast.success("Profile updated successfully")
        return response.data
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Failed to update profile"
      toast.error(errorMessage)
      throw err
    } finally {
      setLoading(false)
    }
  }

  return {
    updateProfile,
    loading,
  }
}
