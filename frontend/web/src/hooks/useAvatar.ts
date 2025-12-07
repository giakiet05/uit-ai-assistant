import { useState } from "react"
import { apiClient } from "@/lib/api"
import { toast } from "sonner"

export function useUploadAvatar() {
  const [loading, setLoading] = useState(false)

  const uploadAvatar = async (file: File) => {
    try {
      setLoading(true)
      const response = await apiClient.uploadAvatar(file)
      if (response.success) {
        toast.success("Avatar uploaded successfully")
        return response.data
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Failed to upload avatar"
      toast.error(errorMessage)
      throw err
    } finally {
      setLoading(false)
    }
  }

  return {
    uploadAvatar,
    loading,
  }
}

export function useDeleteAvatar() {
  const [loading, setLoading] = useState(false)

  const deleteAvatar = async () => {
    console.log("🗑️ useDeleteAvatar: Starting delete")
    try {
      setLoading(true)
      console.log("📡 Calling API deleteAvatar...")
      const response = await apiClient.deleteAvatar()
      console.log("✅ API response:", response)

      if (response.success) {
        toast.success("Avatar deleted successfully")
        return true
      }

      toast.error(response.message || "Failed to delete avatar")
      return false
    } catch (err) {
      console.error("❌ Delete avatar error:", err)
      const errorMessage = err instanceof Error ? err.message : "Failed to delete avatar"
      toast.error(errorMessage)
      throw err
    } finally {
      setLoading(false)
      console.log("🏁 Delete avatar completed")
    }
  }

  return {
    deleteAvatar,
    loading,
  }
}
